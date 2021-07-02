from typing import Iterable
from discord.ext import commands
from engfrosh_common.DatabaseInterface import DatabaseInterface
import logging
import datetime as dt
import traceback

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
        if "debug" in config and config["debug"]:
            self.debug = True
        else:
            self.debug = False
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

        # Print to console
        print(f"\n{level}: {message}")

        # Send to log channels
        await self.send_to_all(f"```\n{level} {dt.datetime.now().isoformat()}: {message}\n```", self.log_channels)

        # Python Logger
        level = level.upper()
        if level in LOG_LEVELS:
            level_number = LOG_LEVELS[level]
        elif level == "EXCEPTION":
            logger.exception(message)
            return
        else:
            level_number = 0

        logger.log(level_number, message)

    async def on_error(self, event_method, *args, **kwargs):
        msg = f'Ignoring exception in {event_method}\n{traceback.format_exc()}'
        await self.log(msg, "EXCEPTION")

    async def on_command_error(self, context, exception):
        # if self.extra_events.get('on_command_error', None):
        #     return

        # if hasattr(context.command, 'on_error'):
        #     return

        # cog = context.cog
        # if cog and commands.Cog._get_overridden_method(cog.cog_command_error) is not None:
        #     return

        msg = f'Ignoring exception in command {context.command}:\n{"".join(traceback.format_exception(type(exception), exception, exception.__traceback__))}'
        await self.log(msg, "EXCEPTION")

    async def error(self, message):
        await self.log(message, "ERROR")

    async def warning(self, message):
        await self.log(message, "WARNING")
