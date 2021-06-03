import discord
from discord.ext import commands
import os
import json
import logging

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)

LOG_LEVEL = logging.DEBUG
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(SCRIPT_NAME)

with open(CURRENT_DIRECTORY + "/config.json") as file:
    config = json.load(file)
    bot_token = config["bot_token"]
    modules = config["modules"]
    prefix = config["prefix"]

client = commands.Bot(prefix)

if __name__ == "__main__":
    LOG_FILE = CURRENT_DIRECTORY + "/{}.log".format(SCRIPT_NAME)
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except PermissionError:
            pass
    logging.basicConfig(level=LOG_LEVEL, filename=LOG_FILE)
    logger.debug("Module started.")
    logger.debug("Log file set as: %s", LOG_FILE)

    #Load Cogs
    for cog in modules:
        print(cog)
        client.load_extension(cog)
        logger.debug('Cog %s loaded', cog)

logger.debug("Set current directory as: %s", CURRENT_DIRECTORY)

@client.event
async def on_ready():
    logger.debug("Logged on as {}".format(client.user))
    #game = discord.Game(name="\'!help\' for info!")
    #await client.change_presence(activity=game)
    await client.change_presence(activity = discord.Game(name="\'!help\' for info!", type=1, url='engfrosh.com'))

@client.command(pass_context=True)
async def superhelp(ctx):
    logger.debug("Help message used in {}".format(ctx.message.channel.guild.name))
    string = "hey, type !react emoji" \

    embed = discord.Embed()
    embed.add_field(name="Bot Usage!", value=string)
    await ctx.channel.send(embed=embed)

@client.command(pass_context=True)
async def react(ctx):
    await ctx.message.add_reaction("🍋")
    await ctx.channel.send("did it work?")

client.run(bot_token)