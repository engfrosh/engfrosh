"""Interface for interacting with Postgres Database."""

# region Imports
import logging
import asyncpg
import uuid
import datetime

from typing import Dict, Iterable, List, Optional, Tuple, Union

from . import Objects
# endregion


logger = logging.getLogger("DatabaseInterface")


class DatabaseInterface():
    """Interface for interacting with Postgres Database."""

    def __init__(self, *, sql_pool: asyncpg.Pool = None, db_credentials: Dict[str, str] = None,
                 allow_development_db=False) -> None:
        """
        Initialize Database Interface.

        Arguments:
            sql_pool: asyncpg pool object to the database
            db_credentials: postgresql credentials in a dictionary
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

        elif allow_development_db:
            self.db = "FAKE"
            logger.warning("Using fake development database")

        else:
            raise NotImplementedError("Does not support non-postgres")

    # region Exceptions

    class NotPostgresError(Exception):
        """Not Postgres Error for postgres only command."""

    class FakeDatabaseError(Exception):
        """Tried running command on fake database."""

    class FinishedScavException(Exception):
        """Exception raised when Team is finished Scavenger."""

    # region Helper Functions

    @property
    def _is_postgres(self) -> bool:
        return self.db == "POSTGRES"

    @property
    def _is_fake(self) -> bool:
        return self.db == "FAKE"

    async def _ensure_pool(self):
        if not self._is_postgres:
            raise self.NotPostgresError

        if not self.pool:
            self.pool = await asyncpg.create_pool(**self.db_credentials)
            self.db_credentials = None
            logger.info("Connection pool created")
        else:
            logger.debug("ensure_pool: pool already exists")

    async def _fetchone(self, sql: str, parameters: Iterable):
        return await self._fetchrow(sql, parameters)

    async def _fetchrow(self, sql: str, parameters: Iterable):
        if self._is_postgres:
            await self._ensure_pool()
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, *parameters)

        elif self._is_fake:
            raise self.FakeDatabaseError

        return row

    async def _fetchall(self, sql, parameters=tuple()):
        if self._is_postgres:
            await self._ensure_pool()
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, *parameters)

        elif self._is_fake:
            raise self.FakeDatabaseError

        return rows

    async def _execute(self, sql, parameters):
        if self._is_postgres:
            await self._ensure_pool()
            logger.debug(f"Executing command '{sql}' with parameters {parameters}")
            async with self.pool.acquire() as conn:
                await conn.execute(sql, *parameters)
            return True

        elif self._is_fake:
            raise self.FakeDatabaseError

        else:
            raise NotImplementedError("Execute currently only written for postgres.")

    def _qp(self, num=1):
        """Alias for _get_query_parameter"""
        return self._get_query_parameter(num)

    def _get_query_parameter(self, num=1):
        if self._is_postgres:
            return f"${num}"
        else:
            raise NotImplementedError("Databases other than Postgres not supported.")
    # endregion

    # region GET methods

    async def get_group_id(self, *, group_name: Optional[str] = None, scav_channel_id=None) -> Union[None, int]:
        """Return the group id if it exists, otherwise None."""

        if self._is_fake:
            return 1

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
        if self._is_fake:
            return 1

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
        if self._is_fake:
            return 1

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
        if self._is_fake:
            return 50

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
        if self._is_fake:
            return "Test Team"

        sql = f"SELECT * FROM frosh_team WHERE group_id = {self._qp()};"
        row = await self._fetchrow(sql, (group_id,))
        if row:
            return row["display_name"]
        else:
            return None

    async def get_team_locked_out_time(self, group_id):
        if self._is_fake:
            return False

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
        if self._is_fake:
            return [Objects.FroshTeam(i + 1, f"Test Team {i+1}", (i % 2) * 15) for i in range(3)]

        """Returns a dictionary where the key is the team_id, and the value is the display name."""
        sql = "SELECT * FROM frosh_team;"
        rows = await self._fetchall(sql)
        lst = []
        for row in rows:
            lst.append(Objects.FroshTeam(row["group_id"], row["display_name"], row["coin_amount"]))
        return lst

    async def get_permission_id(self, name) -> int:
        if self._is_fake:
            return 1

        sql = f"""SELECT * FROM auth_permission WHERE codename = {self._qp()};"""
        row = await self._fetchrow(sql, (name,))
        if row:
            return row["id"]
        else:
            return None

    async def get_groups(self, *, user_id=None) -> Tuple[int]:
        if self._is_fake:
            return (1, 2, 3)

        if not user_id:
            raise ValueError

        sql = f"SELECT * FROM auth_user_groups WHERE user_id = {self._qp()};"
        rows = await self._fetchall(sql, (user_id,))
        lst = []
        for row in rows:
            lst.append(row["group_id"])

        return tuple(lst)

    async def get_all_scav_questions(self) -> List[Objects.ScavQuestion]:
        """Returns a sorted list of scavenger questions from lowest to highest weight."""
        if self._is_fake:
            return [Objects.ScavQuestion(id=i, enabled=True, text=f"Question {i}",
                                         answer=f"answer{i}", weight=i) for i in range(1, 5)]

        logger.debug("Getting all scav questions from database.")

        sql = "SELECT * FROM scavenger_question;"
        rows = await self._fetchall(sql)
        logger.debug(f"Got rows: {rows}")
        if not rows:
            raise Exception("Could not get scav questions.")

        questions = []
        for row in rows:
            questions.append(Objects.ScavQuestion(row=row))

        questions.sort(key=lambda q: q.weight)
        logger.debug(f"Got all questions: {questions}")
        return questions

    async def get_scav_question(self, *, team_id: int) -> Union[None, Objects.ScavQuestion]:
        if self._is_fake:
            return Objects.ScavQuestion(id=1, enabled=True, weight=6, answer="answer", text="Question?")

        sql = f"SELECT * FROM scavenger_team WHERE group_id = {self._qp()};"
        row = await self._fetchrow(sql, (team_id,))
        if not row:
            return None

        qid = row["current_question_id"]

        sql = f"SELECT * FROM scavenger_question WHERE id = {self._qp()};"
        row = await self._fetchrow(sql, (qid,))

        if row:
            return Objects.ScavQuestion(row=row)

        logger.error(f"No Question with id {qid}")
        return None

    async def get_team_scav_hints(self, active_only: bool = True, *,
                                  team_id: int) -> Union[None, List[Objects.ScavHint]]:
        """
        Return the scav hints for a team.

        If active only is True, only provides the active hints for the team.
        """

        if self._is_fake:
            raise NotImplementedError()

        cur_question = await self.get_scav_question(team_id=team_id)
        if not cur_question:
            logger.error(f"Could not get current team question for team: {team_id}")
            return None

        if active_only:
            team = await self.get_scav_team(team_id=team_id)
            if not team:
                logger.error(f"Could not get team with specified id {team_id}")
                return None

            last_hint = await self.get_scav_hint(team.last_hint)
            if not last_hint:
                logger.info(f"Team {team_id} has no active hints.")
                return None

            if last_hint.question == cur_question.id:
                sql = "SELECT * FROM scavenger_hint WHERE (question_id = $1 AND weight <= $2);"

                rows = await self._fetchall(sql, (team.current_question, last_hint.weight))
                if not rows:
                    logger.error(
                        f"Could not get any hints for the current question {team.current_question} for team {team_id}")
                    return None

            else:
                return None

        else:
            sql = "SELECT * FROM scavenger_hint WHERE question_id = $1;"

            rows = await self._fetchall(sql, (cur_question.id,))
            if not rows:
                logger.warning(f"Could not get any hints for question {cur_question}")
                return None

        hints = []
        for row in rows:
            hints.append(Objects.ScavHint(row=row))

        return hints

    async def get_scav_hint(self, hint_id: int) -> Union[None, Objects.ScavHint]:
        """Get the scav hint specified with hint_id."""

        if self._is_fake:
            raise NotImplementedError()

        sql = "SELECT * FROM scavenger_hint WHERE id = $1;"
        row = await self._fetchrow(sql, (hint_id,))
        if not row:
            return None

        return Objects.ScavHint(row=row)

    async def get_scav_channels(self, *, group_id: int) -> List[int]:
        if self._is_fake:
            return [1, 2, 3]

        sql = f"SELECT * FROM discord_bot_manager_scavchannel WHERE group_id = {self._qp()};"

        rows = await self._fetchall(sql, (group_id,))
        if not rows:
            return False

        return [r["channel_id"] for r in rows]

    async def get_scav_team(self, *, team_id: int) -> Union[None, Objects.ScavTeam]:
        """Get the scav team with the specified team id."""

        sql = "SELECT * FROM scavenger_team WHERE group_id = $1;"

        row = await self._fetchone(sql, (team_id,))
        if not row:
            return None

        return Objects.ScavTeam(row=row)

    async def get_all_scav_teams(self) -> List[Objects.ScavTeam]:
        """Get all the scav teams."""

        sql = "SELECT * FROM scavenger_team;"

        rows = await self._fetchall(sql)
        if not rows:
            logger.warning("Did not get any scav teams.")
            return []

        teams = []
        for row in rows:
            teams.append(Objects.ScavTeam(row=row))

        return teams

    async def get_next_hint(self, *, team_id: int) -> Union[None, Objects.ScavHint]:
        """Get the next hint for the team and increment the hint number."""

        team = await self.get_scav_team(team_id=team_id)
        if not team:
            return None

        hints = await self.get_team_scav_hints(False, team_id=team_id)
        if not hints:
            return None

        hints.sort(key=lambda h: h.weight)

        cur_hint = await self.get_scav_hint(team.last_hint)
        if cur_hint in hints:
            i = hints.index(cur_hint)
            next_hint = hints[i + 1]
        else:
            next_hint = hints[0]

        sql = "UPDATE scavenger_team SET last_hint_id = $1;"
        res = await self._execute(sql, (next_hint.id,))
        if not res:
            raise Exception("Error setting team's next hint.")

        res = await self.set_team_locked_out_time(seconds=next_hint.lockout_time, group_id=team_id)
        if not res:
            raise Exception("Could not lock team out.")

        return next_hint

    async def get_all_users_in_group(self, group_id: int) -> List[int]:
        """Returns a list of user ids."""

        sql = "SELECT * FROM auth_user_groups WHERE group_id = $1;"

        rows = await self._fetchall(sql, (group_id,))
        if not rows:
            logger.warning("Did not get any users in group %i", group_id)
            return []

        users = []
        for row in rows:
            users.append(row["user_id"])

        return users

    async def get_discord_user(self, user_id: int) -> Union[None, Objects.DiscordUser]:
        """Get the discord user from the django user."""

        sql = "SELECT * FROM authentication_discorduser WHERE user_id = $1;"

        row = await self._fetchrow(sql, (user_id,))
        if not row:
            logger.warning("Could not discord user for user id %i", user_id)
            return None

        return Objects.DiscordUser(row=row)

    # endregion

    # region UPDATE methods

    async def update_coin_amount(self, change: int, *, group_name=None, group_id=None):
        if self._is_fake:
            return True

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

    async def set_team_locked_out_time(self, group_id: int, minutes: float = 0,
                                       seconds: float = 0, *, end_time=None) -> bool:
        """Set the lockout time for the given team."""

        if self._is_fake:
            return True

        sql = f"""UPDATE scavenger_team
                    SET locked_out_until = {self._qp(1)}
                    WHERE group_id = {self._qp(2)};"""

        if (minutes or seconds) and not end_time:
            end_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes, seconds=seconds)

        if not end_time:
            raise ValueError("Endtime or minutes must be provided")

        if self._is_postgres:
            if type(end_time) is str:
                end_time = datetime.datetime.fromisoformat(end_time)

            if type(end_time) is not datetime.datetime:
                raise TypeError(f"end_time can only be type datetime.datetime or str, not {type(end_time)}")

        await self._execute(sql, (end_time, group_id))

        logger.info(f"Set lockout until time for group {group_id} to {end_time}")

        return True

    async def set_scav_team_unlocked(self, group_id: int):
        """Unlock the specified team."""

        sql = "UPDATE scavenger_team SET locked_out_until = NULL WHERE group_id = $1;"

        await self._execute(sql, (group_id,))

    # endregion

    # region CHECK methods

    async def check_user_in_group(self, user_id: Optional[int] = None, group_name=None,
                                  discord_user_id: int = None, group_id: Optional[int] = None) -> bool:
        """Checks whether the provided user is in the provided group."""
        if self._is_fake:
            return True

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
        if self._is_fake:
            return True

        if not user_id:
            user_id = await self.get_user_id(discord_id=discord_id)

        if not permission_id:
            permission_id = await self.get_permission_id(permission_name)

        if not (user_id and permission_id):
            return False

        # Check single permissions
        sql = f"""SELECT * FROM auth_user_user_permissions
                  WHERE user_id = {self._qp(1)} AND permission_id = {self._qp(2)};"""
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
        if self._is_fake:
            return True

        sql = f"SELECT * FROM auth_group_permissions WHERE group_id = {self._qp(1)} AND permission_id = {self._qp(2)};"

        res = await self._fetchone(sql, (group_id, permission_id))
        if res:
            return True

        return False

    async def check_scavenger_setting_enabled(self, *, id: int = None, name: str = None):
        if self._is_fake:
            return True

        if id and name:
            raise ValueError
        elif id:
            field = "id"
            parameters = (id,)
        elif name:
            field = "name"
            parameters = (name,)
        else:
            raise ValueError

        sql = f"SELECT * FROM scavenger_settings WHERE {field} = {self._qp()};"
        row = await self._fetchrow(sql, parameters)
        if row:
            return row["enabled"]

        return None

    # endregion

    # region Other Actions

    async def increment_question(self, team_id: int, current_question: Objects.ScavQuestion):
        if self._is_fake:
            return True

        logger.debug(f"Incrementing question for team {team_id} for question: {current_question.identifier}")
        questions = await self.get_all_scav_questions()

        i = questions.index(current_question)
        logger.debug(f"Got index of current question: {i}")

        for q in questions[i + 1:]:
            if q.enabled:
                logger.debug(f"Found valid next question {q}")
                sql = f"UPDATE scavenger_team SET current_question_id = {self._qp(1)} WHERE group_id = {self._qp(2)};"
                res = await self._execute(sql, (q.id, team_id))
                if not res:
                    raise Exception("Failed to update current question.")
                logger.info(
                    f"Incremented question for team {team_id} from question {current_question.weight} to {q.weight}")
                return True

        logger.info(f"No more questions found, therefore assuming Team {team_id} has finished scav.")
        sql = f"UPDATE scavenger_team SET current_question_id = NULL, finished = TRUE WHERE group_id = {self._qp()};"
        res = await self._execute(sql, (team_id,))
        if not res:
            raise Exception("Failed to update current question to null.")
        raise self.FinishedScavException

    # endregion
