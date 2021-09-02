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
    async def get_overwrites(self, ctx: commands.Context, channel_id: Optional[int] = None):
        """Get all the permission overwrites for the current channel."""

        if ctx.author.id not in self.config["superadmin"]:  # type: ignore
            return

        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                overwrites = channel.overwrites
            else:
                await ctx.reply("error")
                return

        else:

            overwrites = ctx.channel.overwrites  # type: ignore

        msg = "```\n"
        for k, v in overwrites.items():
            msg += f"{k} {k.id}:\n"
            for p in v:
                if p[1] is not None:
                    msg += f"    {p}\n"
        msg += "```"

        await ctx.send(msg)
        return

    @commands.command()
    async def shutdown(self, ctx):
        """Shuts down and logs out the discord bot."""
        if ctx.author.id in self.config["superadmin"]:
            await ctx.reply("Logging out.")
            await self.bot.log("Logging out.")
            await self.bot.logout()
            exit()

        else:
            return


def setup(bot):
    """Management COG setup."""
    bot.add_cog(Management(bot))
