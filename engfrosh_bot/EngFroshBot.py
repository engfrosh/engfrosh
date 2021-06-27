from typing import Iterable
from discord.ext import commands
from engfrosh_common.DatabaseInterface import DatabaseInterface
import logging

logger = logging.getLogger("EngFroshBot")


class EngFroshBot(commands.Bot):
    def __init__(self, command_prefix, db_int: DatabaseInterface,
                 config: dict, help_command=None, description=None, **options):
        self.db_int = db_int
        self.config = config
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
