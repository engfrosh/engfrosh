"""Discord Management COG."""

from typing import Optional
import discord
from discord.ext import commands
from ...EngFroshBot import EngFroshBot


class Management(commands.Cog):
    """Discord Management Cog"""

    def __init__(self, bot: EngFroshBot) -> None:
        """Management COG init"""
        self.bot = bot
        self.config = bot.config["module_settings"]["management"]

    @commands.command()
    async def purge(self, ctx: commands.Context, channel_id: Optional[str] = None):
        """Purge the channel, only available to superadmin."""

        if ctx.author.id not in self.config["superadmin"]:  # type: ignore
            return

        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.channel.purge()  # type: ignore
        else:
            await ctx.reply("Cannot purge this channel type.")

        return

    @commands.command()
    async def lock(self, ctx: commands.Context, channel_id: Optional[str] = None):
        """Lock the current channel from frosh, facils, and heads."""

        if ctx.author.id not in self.config["superadmin"]:  # type: ignore
            return

    @commands.command()
    async def get_overwrites(self, ctx: commands.Context):
        """Get all the permission overwrites for the current channel."""

        if ctx.author.id not in self.config["superadmin"]:  # type: ignore
            return

        overwrites = ctx.channel.overwrites  # type: ignore
        await ctx.send(overwrites)
        return


def setup(bot):
    """Management COG setup."""
    bot.add_cog(Management(bot))
