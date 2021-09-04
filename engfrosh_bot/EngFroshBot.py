"""Discord Bot Client with EngFrosh specific features."""

import io
from typing import Iterable, Optional
import discord
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
    """Discord Bot Client with additional properties including config and database support."""

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

    async def send_to_all(self, message: str, channels: Iterable[int], *,
                          purge_first: bool = False, file: Optional[discord.File] = None) -> bool:
        """Sends message to all channels with given ids."""
        res = True
        for chid in channels:
            if channel := self.get_channel(chid):
                if purge_first:
                    await channel.purge()
                await channel.send(message, file=file)
            else:
                logger.error(f"Could not get channel with id: {chid}")
                res = False

        return res

    async def log(self, message: str, level: str = "INFO", exc_info=None):
        """Log a message to the bot channels and the logger."""

        # Print to console
        print(f"\n{level}: {message}")

        # Send to log channels
        content = f"\n{level} {dt.datetime.now().isoformat()}: {message}\n"
        if len(content) >= 1900:
            fp = io.StringIO(content)
            file = discord.File(fp, f"{dt.datetime.now().isoformat()}.log")
            await self.send_to_all("", self.log_channels, file=file)

        else:
            await self.send_to_all(f"```{content}```", self.log_channels)

        # Python Logger
        level = level.upper()
        if level in LOG_LEVELS:
            level_number = LOG_LEVELS[level]
        elif level == "EXCEPTION":
            logger.exception(message)
            return
        else:
            level_number = 0

        logger.log(level_number, message, exc_info=exc_info)

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

        trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        msg = f'Ignoring exception in command {context.command}:\n{trace}'
        await self.log(msg, "EXCEPTION")

    async def error(self, message, *, exc_info=None):
        await self.log(message, "ERROR", exc_info=exc_info)

    async def warning(self, message, *, exc_info=None):
        await self.log(message, "WARNING", exc_info=exc_info)
