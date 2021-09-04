"""Object representations of Database Objects."""

from asyncpg import Record
from typing import Optional
import datetime
import dateutil.tz
import logging

logger = logging.getLogger("EngFrosh_Common.Objects")


class FroshTeam:
    def __init__(self, id: int, display_name: str, coin_amount: int = None) -> None:
        self.id = id
        self.name = display_name
        self.coin = coin_amount


class ScavQuestion:
    def __init__(
            self, *, id: int = None, enabled: bool = None, identifier: str = None, text: str = None, weight: int = None,
            answer: str = None, row: Record = None) -> None:

        if not row and not (id, answer):
            raise ValueError("Insufficient arguments")

        if row:
            self.id = row["id"]
            self.enabled = row["enabled"]
            self.identifier = row["identifier"]
            self.text = row["text"]
            self.weight = row["weight"]
            self.answer = row["answer"]
            self.file = row["file"]
            self.display_filename = row["display_filename"]

        else:
            self.id = id
            self.enabled = enabled
            self.identifier = identifier
            self.text = text
            self.weight = weight
            self.answer = answer
            self.file = None
            self.display_filename = None

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, ScavQuestion):
            return NotImplemented

        if self.id == o.id and self.identifier == o.identifier and self.answer == o.answer:
            return True

        return False

    def __str__(self) -> str:
        if self.identifier:
            return self.identifier
        else:
            return f"Question {self.weight}"

    def __repr__(self) -> str:
        return f"<Question: {str(self)} id: {self.id}>"


class ScavHint:
    """Representation of Scav Hints."""

    def __init__(self, *, row: Optional[Record] = None) -> None:
        """Initialized Scavenger Hint Object."""

        if not row:
            raise ValueError()

        if row:
            self.id = row["id"]
            self.question: int = row["question_id"]
            self.text = row["text"]
            self.file: str = row["file"]
            self.display_filename: str = row["display_filename"]
            self.weight = row["weight"]
            self.enabled = row["enabled"]
            self.lockout_time: int = row["lockout_time"]

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, ScavHint):
            return NotImplemented

        if self.id == o.id:
            return True

        return False


class DiscordUser:
    """Representation of a Discord User."""

    def __init__(self, *, row: Optional[Record] = None) -> None:
        """Initialize Discord User."""

        if not row:
            raise ValueError("row currently required.")

        self.id = row["id"]
        self.discord_id = self.id
        self.discord_username = row["discord_username"]
        self.discriminator = row["discriminator"]
        self.user_id = row["user_id"]

    @property
    def full_username(self) -> str:
        """Return the combined username and discriminator."""
        return f"{self.discord_username}#{self.discriminator}"


class ScavTeam:
    """Representation of Scav Teams."""

    def __init__(self, *, row: Optional[Record] = None) -> None:
        """Initialize Scavenger Team Object."""

        if not row:
            raise ValueError()

        if row:
            self.group = row["group_id"]
            self.id = self.group
            self.current_question: int = row["current_question_id"]
            self.locked_out_until: datetime.datetime = row["locked_out_until"]
            self.last_hint = row["last_hint_id"]
            self.last_hint_time = row["last_hint_time"]
            self.hint_cooldown_until = row["hint_cooldown_until"]
            self.finished: bool = row["finished"]

    @property
    def locked_out(self) -> bool:
        """Return a boolean of whether the team is currently locked out of scav."""

        if not self.locked_out_until:
            logger.debug("Team does not have any lock out info.")
            return False

        cur_time = datetime.datetime.now(dateutil.tz.gettz())
        logger.debug(f"Current time: {cur_time}")
        logger.debug(f"Team locked out until: {self.locked_out_until}")

        if cur_time < self.locked_out_until:
            return True

        else:
            return False

    @property
    def on_cooldown(self) -> bool:
        """Return whether a team is currently on hint cooldown."""

        if not self.hint_cooldown_until:
            return False

        cur_time = datetime.datetime.now(dateutil.tz.gettz())
        if cur_time < self.hint_cooldown_until:
            return True

        else:
            return False

    @property
    def lockout_remaining(self) -> str:
        """Return the duration of how much time is remaining in the lockout."""

        if self.locked_out:
            cur_time = datetime.datetime.now(dateutil.tz.gettz())
            duration = self.locked_out_until - cur_time
            return str(duration).split(".")[0]

        else:
            return "00:00"
