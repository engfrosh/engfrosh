from typing import Iterable
from discord.ext import commands
from engfrosh_common.DatabaseInterface import DatabaseInterface
import logging
import datetime as dt

logger = logging.getLogger("EngFroshBot")

LOG_LEVELS = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0
}


class EngFroshBot(commands.Bot):
    def __init__(self, command_prefix, db_int: DatabaseInterface,
                 config: dict, help_command=None, description=None, log_channels=[], **options):
        self.db_int = db_int
        self.config = config
        self.log_channels = log_channels
        super().__init__(command_prefix, description=description, **options)

    async def send_to_all(self, message: str, channels: Iterable[int], *, purge_first=False) -> None:
        """Sends message to all channels with given ids."""
        for chid in channels:
            if channel := self.get_channel(chid):
                if purge_first:
                    await channel.purge()
                await channel.send(message)
            else:
                logger.error(f"Could not get channel with id: {chid}")

    async def log(self, message: str, level: str = "INFO"):
        """Log a message to the bot channels and the logger."""
        level = level.upper()
        if level in LOG_LEVELS:
            level_number = LOG_LEVELS[level]
        else:
            level_number = 0
        logger.log(level_number, message)
        await self.send_to_all(f"```\n{level} {dt.datetime.now().isoformat()}: {message}\n```", self.log_channels)
