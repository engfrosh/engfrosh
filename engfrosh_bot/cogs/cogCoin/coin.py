from discord.ext import commands
from ...EngFroshBot import EngFroshBot
# from engfrosh_common.DatabaseInterface import DatabaseInterface

import logging
import os


logger = logging.getLogger("Cogs.Coin")


class Coin(commands.Cog):
    def __init__(self, bot: EngFroshBot) -> None:
        self.bot = bot
        self.config = bot.config["module_settings"]["coin"]

    @commands.command()
    async def hello(self, ctx):
        await ctx.channel.send("Hello!")

    @commands.command()
    async def coin(self, ctx: commands.Context, team, amount):
        if not self.bot.config["module_settings"]["coin"]["public_commands"]:
            await ctx.message.delete()

        await ctx.channel.send(f"Team: {team} Amount {amount}")

        team_id = await self.bot.db_int.get_frosh_team_id(team_name=team)

        if not team_id:
            await ctx.author.send(f"Sorry, no team called {team}, please try again.")
            return

        res = await self.bot.db_int.update_coin_amount(int(amount), group_id=team_id)

        if res:
            display_name = await self.bot.db_int.get_team_display_name(team_id)
            await ctx.channel.send(f"{display_name} You got {amount} scoin!")
            await self.update_coin_board()
        else:
            logger.error("Could not add coin.")
            await ctx.author.send(f"Setting coin for team: {team} failed.")

    async def update_coin_board(self):
        teams = await self.bot.db_int.get_all_frosh_teams()

        teams.sort(key=lambda team: team.coin, reverse=True)

        msg = "```\nScoin Standings\n==================\n"
        name_padding = 25
        coin_padding = 10
        for i in range(len(teams)):
            msg += "{place}. {team_name} {coin_amount}\n".format(
                place=i + 1, team_name=f"{teams[i].name}{' ' * (name_padding - len(str(teams[i].name)))}",
                coin_amount=f"{teams[i].coin}{' ' * (coin_padding - len(str(teams[i].coin)))}")
        msg += "```"

        for chid in self.config["scoreboard_channels"]:
            if channel := self.bot.get_channel(chid):
                await channel.purge()
                await channel.send(msg)
            else:
                logger.error(f"Could not get channel with id: {chid}")


def setup(bot):
    bot.add_cog(Coin(bot))
