from discord.ext import commands
from discord import Message
from discord.errors import NotFound
# from discord.ext.commands import cog

import logging


logger = logging.getLogger("ModerationCogs")


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, ctx: Message):
        if not ctx.author == self.bot.user:
            # check
            try:
                if self.bot.config["module_settings"]["moderation"]["checkmark"]:
                    await ctx.add_reaction("☑")
            except NotFound:
                logger.info("Message deleted before moderating")


def setup(bot):
    bot.add_cog(Moderation(bot))
