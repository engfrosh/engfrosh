class Message:

    def __init__(self, text="", identifier="", file_path=None, display_filename="") -> None:
        self.identifier = identifier
        self.text = text
        self.file_path = file_path
        self.display_filename = display_filename
