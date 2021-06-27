import logging
from discord.ext import commands
from discord import Message
from discord.errors import NotFound


logger = logging.getLogger("Cogs.Moderation")


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config['module_settings']['moderation']

    @commands.Cog.listener()
    async def on_message(self, ctx: Message):
        if not ctx.author == self.bot.user:

            # check message here

            try:
                if self.config["checkmark"]:
                    await ctx.add_reaction("☑")
            except NotFound:
                logger.info("Message deleted before moderating")


def setup(bot):
    bot.add_cog(Moderation(bot))
