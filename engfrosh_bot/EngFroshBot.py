from discord.ext import commands
from engfrosh_common.DatabaseInterface import DatabaseInterface


class EngFroshBot(commands.Bot):
    def __init__(self, command_prefix, db_int: DatabaseInterface,
                 config: dict, help_command=None, description=None, **options):
        self.db_int = db_int
        self.config = config
        super().__init__(command_prefix, description=description, **options)
