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
            );"""
]

# TODO Sync these tables up better with what Django does and proper database technique, etc

DEFAULT_SQLITE_DB = "sqlite.db"


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

    async def _ensure_pool(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(**self.db_credentials)
            self.db_credentials = None

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

    async def check_user_in_group(self, user_id, group_name=None, group_id=None):
        # TODO Add support for group id passing
        sql = "SELECT group_id FROM auth_user_groups WHERE user_id = ?;"

        if self._is_postgres():
            await self._ensure_pool()

            group_id = self.get_group_id(group_name)

            cursor = self.connection.cursor()
            cursor.execute(sql, (group_id,))

        elif self._is_sqlite():
            pass

    def _is_postgres(self):
        return self.db == "POSTGRES"

    def _is_sqlite(self):
        return self.db == "SQLITE"

    def __del__(self):
        if self._is_sqlite():
            self.connection.close()
