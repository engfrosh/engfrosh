from discord.ext import commands
from discord.ext.commands import cog


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, ctx):
        # check
        print("hello world")
        # await ctx.channel.send("moderated")


def setup(bot):
    bot.add_cog(Moderation(bot))
