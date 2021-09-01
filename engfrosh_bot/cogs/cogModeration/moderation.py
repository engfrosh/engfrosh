"""Moderation COG for Discord Bot."""

import logging
import re
from discord.ext import commands
from discord import Message
from discord.errors import NotFound
from better_profanity import profanity
import better_profanity.constants
from ...EngFroshBot import EngFroshBot

logger = logging.getLogger("Cogs.Moderation")

better_profanity.constants.ALLOWED_CHARACTERS.remove("*")


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

        message = str(ctx.content)
        if self.profanity.contains_profanity(message) or self.regex_profanity.search(message):
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
