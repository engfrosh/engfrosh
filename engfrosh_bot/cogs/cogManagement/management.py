"""Discord Management COG."""

import logging
import os
from typing import List, Optional
import discord
from discord.ext import commands

from engfrosh_common import Objects
from ...EngFroshBot import EngFroshBot

logger = logging.getLogger("CogManagement")


class Management(commands.Cog):
    """Discord Management Cog"""

    def __init__(self, bot: EngFroshBot) -> None:
        """Management COG init"""
        self.bot = bot
        self.config = bot.config["module_settings"]["management"]

    @commands.command()
    async def purge(self, ctx: commands.Context, channel_id: Optional[str] = None):
        """Purge the channel, only available to admin."""

        if ctx.author.id not in self.config["superadmin"] and ctx.author.id not in self.config["admin"]:  # type: ignore
            return

        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.channel.purge()  # type: ignore
        else:
            await ctx.reply("Cannot purge this channel type.")

        return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """On raw reaction add handling."""

        channel_id = payload.channel_id
        emoji = payload.emoji
        user_id = payload.user_id

        if user_id == self.bot.user.id:
            return

        reaction_type = payload.event_type
        message_id = payload.message_id

        if message_id not in self.config["pronoun_message"]:
            return

        guild = self.bot.get_guild(self.bot.config["guild"])
        if not guild:
            await self.bot.error(f"Could not get guild {self.bot.config['guild']}")
            return

        member = payload.member

        if emoji.name == "1️⃣":
            role = guild.get_role(self.config["pronouns"]["he"])
            await member.add_roles(role)
        elif emoji.name == "2️⃣":
            role = guild.get_role(self.config["pronouns"]["she"])
            await member.add_roles(role)
        elif emoji.name == "3️⃣":
            role = guild.get_role(self.config["pronouns"]["they"])
            await member.add_roles(role)
        elif emoji.name == "4️⃣":
            role = guild.get_role(self.config["pronouns"]["ask"])
            await member.add_roles(role)
        else:
            await self.bot.log(
                f"Channel: {channel_id} Emoji: {emoji} user_id: {user_id} reaction_type: {reaction_type}")
            return

    @commands.command()
    async def send_pronoun_message(self, ctx: commands.Context):
        """Send pronoun message in this channel."""

        if ctx.author.id not in self.config["superadmin"] + self.config["admin"]:
            return

        await ctx.message.delete()

        message = await ctx.channel.send(
            "Select your pronouns:\n:one: He/Him\n:two: She/Her\n:three: They/Them\n:four: Ask Me")

        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await message.add_reaction("3️⃣")
        await message.add_reaction("4️⃣")

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

    @commands.command()
    async def distribute_soopp_bingo(self, ctx: commands.Context):
        """Message all frosh a soopp bingo card."""

        if ctx.author.id not in self.config["superadmin"]:
            return

        path = "offline-files/soopp-bingo"
        bingo_cards = [path + "/" + f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        logger.debug("Got bingo cards:")
        for bc in bingo_cards:
            logger.debug(bc)

        group_id = await self.bot.db_int.get_group_id(group_name="Frosh")
        if not group_id:
            await self.bot.error("Could not get group id for Frosh group.")
            return

        all_frosh = await self.bot.db_int.get_all_users_in_group(group_id)
        discord_users: List[Objects.DiscordUser] = []
        for frosh in all_frosh:
            discord_id = await self.bot.db_int.get_discord_user(frosh)
            if not discord_id:
                await self.bot.log(f"Could not get discord username for frosh id: {frosh}", "WARNING")

            else:
                discord_users.append(discord_id)

        if len(discord_users) > len(bingo_cards):
            await self.bot.error("More frosh than bingo cards, exiting.")
            return

        successes = 0
        failures = 0
        for i in range(len(discord_users)):
            try:
                usr = await self.bot.fetch_user(discord_users[i].id)
                await usr.send(content="Here is your SOOPP bingo card!",
                               file=discord.File(bingo_cards[i], "SOOPP Bingo Card.pdf"))
                successes += 1
            except Exception as e:
                await self.bot.error(
                    f"Could not message bingo card {bingo_cards[i]} to {discord_users[i].full_username}. \
                    See log for details", exc_info=e)
                failures += 1

        final_msg = f"Sent bingo cards to {successes}. Had {failures} failures."
        await ctx.reply(final_msg)
        await self.bot.log(final_msg)
        return


def setup(bot):
    """Management COG setup."""
    bot.add_cog(Management(bot))
