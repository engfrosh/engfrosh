import logging
from discord.ext import commands
from discord import Message
from discord.errors import NotFound
from better_profanity import profanity
from ...EngFroshBot import EngFroshBot

logger = logging.getLogger("Cogs.Moderation")


class Moderation(commands.Cog):
    def __init__(self, bot: EngFroshBot):
        self.bot = bot
        self.config = bot.config['module_settings']['moderation']
        # TODO add way to get additional words from the database.
        self.profanity = profanity
        self.profanity.add_censor_words(self.config['additional_words'])

    @commands.Cog.listener()
    async def on_message(self, ctx: Message):

        if ctx.author == self.bot.user:
            return

        if ctx.channel.id in self.config["ignored_channels"]:
            try:
                if self.config["checkmark"]:
                    await ctx.add_reaction("🟨")
            except NotFound:
                pass
            return

        if self.profanity.contains_profanity(str(ctx.content)):
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
            try:
                if self.config["checkmark"]:
                    await ctx.add_reaction("☑")
            except NotFound:
                pass


def setup(bot):
    bot.add_cog(Moderation(bot))
