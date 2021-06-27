from discord.ext import commands
from ...EngFroshBot import EngFroshBot
# from engfrosh_common.DatabaseInterface import DatabaseInterface

import logging


logger = logging.getLogger("Cogs.Coin")


class Coin(commands.Cog):
    def __init__(self, bot: EngFroshBot) -> None:
        self.bot = bot
        self.db = bot.db_int
        self.config = bot.config["module_settings"]["coin"]

    @commands.command()
    async def hello(self, ctx):
        await ctx.channel.send("Hello!")

    @commands.command()
    async def coin(self, ctx: commands.Context, team, amount):
        allowed = await self.db.check_user_has_permission(discord_id=ctx.author.id, permission_name=self.config["permission"])
        if not allowed:
            await ctx.message.reply("Sorry, you don't have the permission to do that.")
            return

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

        cur_place = 0
        cur_coin = None
        next_place = 1

        for team in teams:
            s = "{place}. {team_name} {coin_amount}\n"

            team_name = team.name
            coin_amount = team.coin

            if coin_amount == cur_coin:
                # If there is a tie
                place = cur_place
                next_place += 1
            else:
                place = next_place
                cur_place = next_place
                next_place += 1
                cur_coin = coin_amount

            msg += s.format(
                place=place, team_name=f"{team_name}{' ' * (name_padding - len(str(team_name)))}",
                coin_amount=f"{coin_amount}{' ' * (coin_padding - len(str(coin_amount)))}")
        msg += "```"

        for chid in self.config["scoreboard_channels"]:
            if channel := self.bot.get_channel(chid):
                await channel.purge()
                await channel.send(msg)
            else:
                logger.error(f"Could not get channel with id: {chid}")


def setup(bot):
    bot.add_cog(Coin(bot))
