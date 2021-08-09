"""Object representation of a Discord Message."""


class Message:
    """Object representation of a Discord Message."""

    def __init__(self, text="", identifier="", file_path=None, display_filename="") -> None:
        """Create a Discord message representation."""
        self.identifier = identifier
        self.text = text
        self.file_path = file_path
        self.display_filename = display_filename
