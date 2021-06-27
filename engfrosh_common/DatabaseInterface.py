from sqlite3.dbapi2 import IntegrityError
from typing import List, Tuple
import asyncpg
import sqlite3
import uuid
import datetime
from . import Objects

try:
    from .SQLITE_INIT import SQLITE_INIT
except ModuleNotFoundError:
    from SQLITE_INIT import SQLITE_INIT


import logging
import os


CURRENT_DIRECTORY = os.path.dirname(__file__)
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]

LOG_LEVEL = logging.DEBUG

logger = logging.getLogger(SCRIPT_NAME)


DEFAULT_SQLITE_DB = "default_name.db"


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
            logger.info("DatabaseInterface created for Postgres with sql_pool object")

        elif db_credentials:
            self.db = "POSTGRES"
            self.pool = None
            self.db_credentials = db_credentials
            logger.info("DatabaseInterface created for Postgres with database credentials")

        else:
            self.db = "SQLITE"
            if not sqlite_filename:
                sqlite_filename = DEFAULT_SQLITE_DB

            self.connection = sqlite3.connect(sqlite_filename)
            self.connection.row_factory = sqlite3.Row

            logger.info(f"DatabaseInterface created for SQLite at {sqlite_filename}")

            for command in SQLITE_INIT:
                self.connection.cursor().execute(command)
            logger.debug("Initialized SQLite Database")

    # region GET methods

    async def get_group_id(self, *, group_name=None, scav_channel_id=None):
        if group_name:
            sql = f"SELECT id FROM auth_group WHERE name = {self._qp()};"
            row = await self._fetchrow(sql, (group_name,))
            if row:
                return row["id"]
            else:
                return None

        elif scav_channel_id:
            sql = f"SELECT group_id FROM discord_bot_manager_scavchannel WHERE channel_id = {self._qp()};"
            row = await self._fetchrow(sql, (scav_channel_id,))
            if row:
                return row["group_id"]
            else:
                return None

        else:
            raise NotImplementedError("Must pass one parameter to get group id.")

    async def get_frosh_team_id(self, *, team_name=None):
        """Name can either be a team display name or the group name. Group name takes priority."""
        if team_name:
            id = await self.get_group_id(group_name=team_name)
            if not id:
                sql = f"SELECT * FROM frosh_team WHERE display_name = {self._qp()};"
                row = await self._fetchrow(sql, (team_name,))
                if row:
                    id = row["group_id"]
        else:
            raise ValueError

        return id

    async def get_user_id(self, *, discord_id=None):

        if discord_id:
            sql = f"SELECT * FROM authentication_discorduser WHERE id = {self._qp()};"
            row = await self._fetchrow(sql, (discord_id,))
            if row:
                return row["user_id"]
            else:
                return None

        else:
            raise NotImplementedError

    async def get_coin_amount(self, *, group_name=None, group_id=None):
        if not group_id and group_name:
            group_id = await self.get_group_id(group_name=group_name)
        if group_id:
            sql = f"SELECT * FROM frosh_team WHERE group_id = {self._qp()};"
            row = await self._fetchrow(sql, (group_id,))
            if row:
                return row["coin_amount"]
            else:
                return None
        else:
            logger.warning("No arguments passed to get_coin_amount.")
            return None

    async def get_team_display_name(self, group_id):
        sql = f"SELECT * FROM frosh_team WHERE group_id = {self._qp()};"
        row = await self._fetchrow(sql, (group_id,))
        if row:
            return row["display_name"]
        else:
            return None

    async def get_team_locked_out_time(self, group_id):
        sql = f"SELECT * FROM scavenger_team WHERE group_id = {self._qp()};"

        row = await self._fetchone(sql, (group_id,))
        if not row:
            # None if the team does not exist
            return None

        if not row["locked_out_until"]:
            # False if team is not locked out
            return False

        locked_out_time = row["locked_out_until"]
        if type(locked_out_time) is str:
            locked_out_time = datetime.datetime.fromisoformat(locked_out_time)

        return locked_out_time

    async def get_all_frosh_teams(self) -> List[Objects.FroshTeam]:
        """Returns a dictionary where the key is the team_id, and the value is the display name."""
        sql = "SELECT * FROM frosh_team;"
        rows = await self._fetchall(sql)
        lst = []
        for row in rows:
            lst.append(Objects.FroshTeam(row["group_id"], row["display_name"], row["coin_amount"]))
        return lst

    async def get_permission_id(self, name) -> int:
        sql = f"""SELECT * FROM auth_permission WHERE codename = {self._qp()};"""
        row = await self._fetchrow(sql, (name,))
        if row:
            return row["id"]
        else:
            return None

    async def get_groups(self, *, user_id=None) -> Tuple[int]:
        if not user_id:
            raise ValueError

        sql = f"SELECT * FROM auth_user_groups WHERE user_id = {self._qp()};"
        rows = await self._fetchall(sql, (user_id,))
        lst = []
        for row in rows:
            lst.append(row["group_id"])

        return tuple(lst)

    # endregion

    # region UPDATE methods

    async def update_coin_amount(self, change: int, *, group_name=None, group_id=None):
        if not group_id and group_name:
            group_id = await self.get_group_id(group_name=group_name)
        if group_id:
            sql = f"UPDATE frosh_team SET coin_amount = coin_amount + {self._qp(1)} WHERE group_id = {self._qp(2)};"
            await self._execute(sql, (change, group_id))
            logger.info(f"Adjusted coin for team with id: {group_id} by {change}.")
            return True

        else:
            logger.error("No group passed to update_coin_amount.")
            return False
    # endregion

    # region SET methods
    async def set_discord_command_status(self, command_id, status, error_msg=""):
        sql = f"""UPDATE discord_bot_manager_discordcommandstatus
                    SET status = {self._qp(1)}
                    WHERE command_id = {self._qp(2)};"""
        await self._execute(sql, (status, uuid.UUID(command_id)))
        logger.info(f"Set Discord Command {command_id} to {status}")

    async def set_team_locked_out_time(self, group_id, minutes=None, *, end_time=None):
        sql = f"""UPDATE scavenger_team
                    SET locked_out_until = {self._qp(1)}
                    WHERE group_id = {self._qp(2)};"""

        if minutes and not end_time:
            end_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)

        if not end_time:
            raise ValueError("Endtime or minutes must be provided")

        if self._is_postgres():
            if type(end_time) is str:
                end_time = datetime.datetime.fromisoformat(end_time)

            if type(end_time) is not datetime.datetime:
                raise TypeError(f"end_time can only be type datetime.datetime or str, not {type(end_time)}")

        elif self._is_sqlite():
            if type(end_time) is datetime.datetime:
                end_time = end_time.isoformat()

            if type(end_time) is not str:
                raise TypeError(f"end_time can only be type datetime.datetime or str, not {type(end_time)}")

        await self._execute(sql, (end_time, group_id))

        logger.info(f"Set lockout until time for group {group_id} to {end_time}")

    # endregion

    # region CHECK methods

    async def check_user_in_group(self, user_id=None, group_name=None, discord_user_id=None, group_id=None):
        sql = f"SELECT * FROM auth_user_groups WHERE user_id = {self._qp(1)} AND group_id = {self._qp(2)};"

        if not group_id:
            group_id = await self.get_group_id(group_name=group_name)

        if not user_id:
            user_id = await self.get_user_id(discord_id=discord_user_id)

        row = await self._fetchone(sql, (user_id, group_id,))
        if row:
            return True
        else:
            return False

    async def check_user_has_permission(self, user_id=None, discord_id=None, permission_name=None, permission_id=None):
        if not user_id:
            user_id = await self.get_user_id(discord_id=discord_id)

        if not permission_id:
            permission_id = await self.get_permission_id(permission_name)

        if not (user_id and permission_id):
            return False

        # Check single permissions
        sql = f"SELECT * FROM auth_user_user_permissions WHERE user_id = {self._qp(1)} AND permission_id = {self._qp(2)};"
        row = await self._fetchrow(sql, (user_id, permission_id))
        if row:
            return True

        # Check group permissions
        groups = await self.get_groups(user_id=user_id)
        for group_id in groups:
            res = await self.check_group_has_permission(group_id=group_id, permission_id=permission_id)
            if res:
                return True

        return False

    async def check_group_has_permission(self, *, group_id=None, permission_id=None):
        sql = f"SELECT * FROM auth_group_permissions WHERE group_id = {self._qp(1)} AND permission_id = {self._qp(2)};"

        res = await self._fetchone(sql, (group_id, permission_id))
        if res:
            return True

        return False

    # endregion

    # region ADD methods

    async def add_group(self, group_name):
        """Then returns the new group id"""
        if self._is_sqlite():
            cur = self.connection.cursor()
            try:
                cur.execute(""" INSERT INTO auth_group(name) VALUES(?)""", (group_name,))
                self.connection.commit()
            except IntegrityError:
                logger.error("IntegrityError, could not add group. A group with that name probably already exists.")
                return None
            return cur.lastrowid
        else:
            raise NotImplementedError("Adding groups not currently supported outside SQLite")

    async def add_discord_user(self, discord_id, user_id, discord_username=None, discriminator=None):
        sql = """INSERT INTO authentication_discorduser(id,discord_username,discriminator,user_id) VALUES(?,?,?,?);"""

        if self._is_sqlite():
            cur = self.connection.cursor()
            try:
                cur.execute(sql, (discord_id, discord_username, discriminator, user_id))
            except IntegrityError:
                logger.error("IntegrityError, could not add Discord user. The user probably already exists.")
            self.connection.commit()
            return True
        else:
            raise NotImplementedError("Adding groups not currently supported outside SQLite")

    async def add_user_to_group(self, user_id, *, group_name=None, group_id=None):
        sql = """INSERT INTO auth_user_groups(user_id,group_id) VALUES(?,?)"""

        if not group_id:
            group_id = await self.get_group_id(group_name=group_name)

        if self._is_sqlite():
            cur = self.connection.cursor()
            cur.execute(sql, (user_id, group_id,))
            self.connection.commit()
            return True
        else:
            raise NotImplementedError("Adding groups not currently supported outside SQLite")

    async def add_scav_channel(self, channel_id, group_id):
        if self._is_sqlite():
            sql = """INSERT INTO discord_bot_manager_scavchannel(channel_id,group_id) VALUES(?,?)"""
            cur = self.connection.cursor()
            try:
                cur.execute(sql, (channel_id, group_id))
            except IntegrityError:
                logger.error("IntegrityError, could not add scav channel. The channel probably already exists.")
                return False
            self.connection.commit()
            return True
        else:
            raise NotImplementedError("Adding Scav channels is not currently supported outside SQLite")

    async def add_frosh_team(self, group_id, display_name=None):
        if self._is_sqlite():
            sql = """INSERT INTO frosh_team(group_id,display_name) VALUES(?,?);"""
            cur = self.connection.cursor()
            try:
                cur.execute(sql, (group_id, display_name))
            except IntegrityError:
                logger.error("IntegrityError, could not add team. The team probably already exists.")
                return False
            self.connection.commit()
            return True
        else:
            raise NotImplementedError("Adding Scav channels is not currently supported outside SQLite")

    async def add_scavenger_team(self, group_id):
        if self._is_sqlite():
            sql = """INSERT INTO scavenger_team(group_id) VALUES(?);"""
            cur = self.connection.cursor()
            try:
                cur.execute(sql, (group_id,))
            except IntegrityError:
                logger.error("IntegrityError, could not add team. The team probably already exists.")
                return False
            self.connection.commit()
            logger.info(f"Added scavenger team with id {group_id}")
            return True
        else:
            raise NotImplementedError("Adding scavenger teams only supported with SQLite")

    # endregion

    # region Helper Functions

    async def _ensure_pool(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(**self.db_credentials)
            self.db_credentials = None
            logger.info("Connection pool created")
        else:
            logger.debug("ensure_pool: pool already exists")

    async def _fetchone(self, sql, parameters):
        return await self._fetchrow(sql, parameters)

    async def _fetchrow(self, sql, parameters):
        if self._is_postgres():
            await self._ensure_pool()
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, *parameters)

        elif self._is_sqlite():
            cur = self.connection.cursor()
            cur.execute(sql, parameters)
            row = cur.fetchone()

        return row

    async def _fetchall(self, sql, parameters=tuple()):
        if self._is_postgres():
            await self._ensure_pool()
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, *parameters)

        elif self._is_sqlite():
            cur = self.connection.cursor()
            cur.execute(sql, parameters)
            rows = cur.fetchall()

        return rows

    async def _execute(self, sql, parameters):
        if self._is_postgres():
            await self._ensure_pool()
            logger.debug(f"Executing command '{sql}' with parameters {parameters}")
            async with self.pool.acquire() as conn:
                await conn.execute(sql, *parameters)
            return True

        elif self._is_sqlite():
            cur = self.connection.cursor()
            cur.execute(sql, parameters)
            self.connection.commit()

        else:
            raise NotImplementedError("Execute currently only written for postgres.")

    def _is_postgres(self):
        return self.db == "POSTGRES"

    def _is_sqlite(self):
        return self.db == "SQLITE"

    def _qp(self, num=1):
        """Alias for _get_query_parameter"""
        return self._get_query_parameter(num)

    def _get_query_parameter(self, num=1):
        if self._is_sqlite():
            return "?"
        elif self._is_postgres():
            return f"${num}"
        else:
            raise NotImplementedError("Databases other than Postgres or SQLite not supported.")
    # endregion

    def __del__(self):
        if self._is_sqlite():
            self.connection.close()
