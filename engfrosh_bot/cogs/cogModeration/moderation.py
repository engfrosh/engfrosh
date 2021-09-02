"""Moderation COG for Discord Bot."""

import logging
import re
import confusables

from discord.ext import commands
from discord import Message
from discord.errors import NotFound
from better_profanity import profanity
import better_profanity.constants
from ...EngFroshBot import EngFroshBot

logger = logging.getLogger("Cogs.Moderation")

better_profanity.constants.ALLOWED_CHARACTERS.remove("*")

COUNTRY_CODES = {
    "\U0001f1e6": "a", "\U0001f1e7": "b", "\U0001f1e8": "c", "\U0001f1e9": "d", "\U0001f1ea": "e", "\U0001f1eb": "f",
    "\U0001f1ec": "g", "\U0001f1ed": "h", "\U0001f1ee": "i", "\U0001f1ef": "j", "\U0001f1f0": "k", "\U0001f1f1": "l",
    "\U0001f1f2": "m", "\U0001f1f3": "n", "\U0001f1f4": "o", "\U0001f1f5": "p", "\U0001f1f6": "q", "\U0001f1f7": "r",
    "\U0001f1f8": "s", "\U0001f1f9": "t", "\U0001f1fa": "u", "\U0001f1fb": "v", "\U0001f1fc": "w", "\U0001f1fd": "x",
    "\U0001f1fe": "y", "\U0001f1ff": "z", }


class Moderation(commands.Cog):
    """Discord Moderation COG."""

    def __init__(self, bot: EngFroshBot):
        """Initialize Moderation COG."""

        self.bot = bot
        self.config = bot.config['module_settings']['moderation']
        # TODO add way to get additional words from the database.
        self.profanity = profanity
        self.profanity.add_censor_words(self.config['additional_words'])

        logger.info(f"Using additional regex: {self.config['regex_profanity']}")
        self.regex_profanity = re.compile(self.config["regex_profanity"], flags=re.UNICODE)

    def contains_profanity(self, raw_msg: str) -> bool:
        """Checks if the message contains profanity."""

        if self.profanity.contains_profanity(raw_msg) or self.regex_profanity.search(raw_msg):
            return True

        # replace any country codes
        replaced_message = raw_msg
        if any(c in raw_msg for c in COUNTRY_CODES.keys()):
            for search, replace in COUNTRY_CODES.items():
                replaced_message = replaced_message.replace(search, replace)

            if self.profanity.contains_profanity(replaced_message) or self.regex_profanity.search(replaced_message):
                return True

        normalized = confusables.normalize(replaced_message, True)
        logger.debug(f"Normalized: {normalized}")
        for norm in normalized:
            if self.profanity.contains_profanity(norm) or self.regex_profanity.search(norm):
                return True

        return False

    @commands.Cog.listener()
    async def on_message(self, ctx: Message):

        if ctx.author == self.bot.user:
            return

        if ctx.channel.id in self.config["ignored_channels"]:
            try:
                if self.bot.debug:
                    await ctx.add_reaction("🟨")
            except NotFound:
                pass
            return

        message = ctx.content
        if self.contains_profanity(message):
            # Delete Message
            try:
                await ctx.delete()
            except NotFound:
                pass

            # Report Message
            report_form = self.config['report_message']
            msg = report_form.format(author=f"<@{ctx.author.id}>",
                                     channel=f"<#{ctx.channel.id}>",
                                     content=f"{ctx.content}")
            await self.bot.send_to_all(msg, self.config['report_channels'])

            # Tell User
            form = self.config['profanity_message']
            msg = f"<@{ctx.author.id}> {form}"

            if self.config['reply']['channel']:
                await ctx.channel.send(msg)
            if self.config['reply']['dm']:
                await ctx.author.send(msg)

        else:
            logger.debug(f"Allowed message: {message}")
            try:
                if self.bot.debug:
                    await ctx.add_reaction("☑")
            except NotFound:
                pass


def setup(bot):
    bot.add_cog(Moderation(bot))
