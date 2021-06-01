import asyncpg
import sqlite3

SQLITE_INIT = [
    """ CREATE TABLE IF NOT EXISTS auth_group (
            id integer PRIMARY KEY,
            name text NOT NULL
            );""",
    """ CREATE TABLE IF NOT EXISTS auth_user_groups (
            id integer PRIMARY KEY,
            user_id integer NOT NULL,
            group_id integer NOT NULL
            );""",
    """ CREATE TABLE IF NOT EXISTS authentication_discorduser (
            id integer PRIMARY KEY,
            discord_username text,
            discriminator integer, 
            user_id NOT NULL
            );"""
]

# TODO Sync these tables up better with what Django does and proper database technique, etc

DEFAULT_SQLITE_DB = "default.db"


class DatabaseInterface():

    def __init__(self, *, sql_pool: asyncpg.Pool = None, db_credentials: dict = None, sqlite_filename=None) -> None:
        """
        Arguments:
            sql_pool: asyncpg pool object to the database
            db_credentials: postgresql credentials in a dictionary
            sqlite_filename: filename/path to the sqlite file to open / create
        """

        if sql_pool:
            self.db = "POSTGRES"
            self.pool = sql_pool
            self.db_credentials = None

        elif db_credentials:
            self.db = "POSTGRES"
            self.pool = None
            self.db_credentials = db_credentials

        else:
            self.db = "SQLITE"
            if not sqlite_filename:
                sqlite_filename = DEFAULT_SQLITE_DB

            self.connection = sqlite3.connect(sqlite_filename)
            self.connection.row_factory = sqlite3.Row

            for command in SQLITE_INIT:
                self.connection.cursor().execute(command)

    async def get_group_id(self, group_name):
        sql = "SELECT id FROM auth_group WHERE name = ?;"
        row = await self._fetchrow(sql, (group_name,))
        return row["id"]

    async def add_group(self, group_name):
        """Then returns the new group id"""
        if self._is_sqlite():
            cur = self.connection.cursor()
            cur.execute(""" INSERT INTO auth_group(name) VALUES(?)""", (group_name,))
            self.connection.commit()
            return cur.lastrowid
        else:
            raise NotImplementedError("Adding groups not currently supported outside SQLite")

    async def check_user_in_group(self, user_id=None, group_name=None, discord_user_id=None, group_id=None):
        sql = "SELECT * FROM auth_user_groups WHERE user_id = ? AND group_id = ?;"

        if not group_id:
            group_id = self.get_group_id(group_name)

        if not user_id:
            user_id = await self.get_user_id(discord_id=discord_user_id)

        row = await self._fetchone(sql, (user_id, group_id,))
        if row:
            return True
        else:
            return False

    async def get_user_id(self, *, discord_id=None):

        if discord_id:
            sql = "SELECT * FROM authentication_discorduser WHERE id = ?;"
            row = await self._fetchrow(sql, (discord_id,))
            if row:
                return row["user_id"]
            else:
                return None
                
        else:
            raise NotImplementedError

    async def add_discord_user(self, discord_id, user_id, discord_username=None, discriminator=None):
        sql = """INSERT INTO authentication_discorduser(id,discord_username,discriminator,user_id) VALUES(?,?,?,?);"""

        if self._is_sqlite():
            cur = self.connection.cursor()
            cur.execute(sql, (discord_id, discord_username, discriminator, user_id))
            self.connection.commit()
            return True
        else:
            raise NotImplementedError("Adding groups not currently supported outside SQLite")

    async def add_user_to_group(self, user_id, group_name=None, group_id=None):
        sql = """INSERT INTO auth_user_groups(user_id,group_id) VALUES(?,?)"""

        if not group_id:
            group_id = await self.get_group_id(group_name)

        if self._is_sqlite():
            cur = self.connection.cursor()
            cur.execute(sql, (user_id, group_id,))
            self.connection.commit()
            return True
        else:
            raise NotImplementedError("Adding groups not currently supported outside SQLite")

    # region Helper Functions

    async def _ensure_pool(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(**self.db_credentials)
            self.db_credentials = None

    async def _fetchone(self, sql, parameters):
        return await self._fetchrow(sql, parameters)

    async def _fetchrow(self, sql, parameters):
        if self._is_postgres():
            await self._ensure_pool()
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, parameters)

        elif self._is_sqlite():
            cur = self.connection.cursor()
            cur.execute(sql, parameters)
            row = cur.fetchone()

        return row

    async def _fetchall(self, sql, parameters):
        if self._is_postgres():
            await self._ensure_pool()
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, parameters)

        elif self._is_sqlite():
            cur = self.connection.cursor()
            cur.execute(sql, parameters)
            rows = cur.fetchall()

        return rows

    # async def _execute(self, sql, parameters):
    #     if self._is_sqlite():

    def _is_postgres(self):
        return self.db == "POSTGRES"

    def _is_sqlite(self):
        return self.db == "SQLITE"
    # endregion

    def __del__(self):
        if self._is_sqlite():
            self.connection.close()
