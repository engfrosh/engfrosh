"""Object representations of Database Objects."""

from asyncpg import Record
from typing import Optional


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
            self.lockout_time = row["lockout_time"]


class ScavTeam:
    """Representation of Scav Teams."""

    def __init__(self, *, row: Optional[Record] = None) -> None:
        """Initialize Scavenger Team Object."""

        if not row:
            raise ValueError()

        if row:
            self.group = row["group_id"]
            self.id = self.group
            self.current_question = row["current_question_id"]
            self.locked_out_until = row["locked_out_until"]
            self.last_hint = row["last_hint_id"]
            self.last_hint_time = row["last_hint_time"]

    @property
    def locked_out(self) -> bool:
        """Return a boolean of whether the team is currently locked out of scav."""
        raise NotImplementedError()
