"""Starting point for EngFrosh main Discord bot."""

import typing
import discord
import sys
import logging
import os
import json
import threading
import asyncio
import yaml
from .EngFroshBot import EngFroshBot

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]

# Hack for development to get around import issues
sys.path.append(PARENT_DIRECTORY)
from engfrosh_common.DatabaseInterface import DatabaseInterface  # noqa E402

logger = logging.getLogger(SCRIPT_NAME)

CONFIG_FILE = CURRENT_DIRECTORY + "/bot_config.yaml"

# region Load Configuration Settings

with open(CONFIG_FILE) as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)

# region Logging Setup
if __name__ == "__main__":
    LOG_FILE = CURRENT_DIRECTORY + "/{}.log".format(SCRIPT_NAME)
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except PermissionError:
            pass
    logging.basicConfig(filename=LOG_FILE, level=config["log_level"].upper())
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel("INFO")
    logging.getLogger().addHandler(stream_handler)
    logger.info("Log file set as: %s", LOG_FILE)
# endregion

if config["modules"]["rabbitmq"]:
    from . import rabbit_listener

# Load Credentials
if config["credentials"]["relative_path"]:
    path = CURRENT_DIRECTORY + "/" + config["credentials"]["relative_path"]
else:
    path = config["credentials"]["absolute_path"]

with open(path) as f:
    credentials = json.load(f)

# endregion


if config["modules"]["postgres"]:
    db_int = DatabaseInterface(db_credentials=credentials["database_credentials"])
else:
    db_int = DatabaseInterface(allow_development_db=config["debug"])

client = EngFroshBot(config["bot_prefix"], db_int=db_int, config=config, log_channels=config["bot_log_channel"])

for cog in config["modules"]["cogs"]:
    client.load_extension(cog)
    logger.debug('Cog %s loaded', cog)

# region Discord Events


@client.event
async def on_ready():
    """Strats Discord bot and RabbitMQ thread if configured."""

    logger.debug("Logged on as {}".format(client.user))
    await client.change_presence(activity=discord.Game(name="\'!help\' for info!", type=1, url='engfrosh.com'))

    # region Launch Queue Listener
    # You shouldn't have to change anything in here.
    # To add more functions add them to handle_queued_command
    if config["modules"]["rabbitmq"]:
        discord_loop = asyncio.get_running_loop()
        host = config["module_settings"]["rabbitmq"]["host"]
        queue = config["module_settings"]["rabbitmq"]["queue"]
        rabbit_thread = threading.Thread(target=rabbit_listener.rabbit_main,
                                         args=(discord_loop, discord_queue_callback, host, queue))
        rabbit_thread.start()
    # endregion

    await client.log("Logged on and ready...")

    return


@client.command(pass_context=True)
async def superhelp(ctx):
    """The overarching help function for the bot, lists available commands."""

    logger.debug("Help message used in {}".format(ctx.message.channel.guild.name))
    string = "hey, type !react emoji" \

    embed = discord.Embed()
    embed.add_field(name="Bot Usage!", value=string)
    await ctx.channel.send(embed=embed)


@client.command(pass_context=True)
async def react(ctx):
    """TEST FUNCTION. Add a reaction to the message."""
    await ctx.message.add_reaction("🍋")


@client.event
async def on_reaction_add(reaction, user):
    """Reacts to the message when the user reacts to one of the bot's messagges."""
    if reaction.message.author == client.user:
        if reaction.emoji == '👍':
            await reaction.message.channel.send('Hi there!')
    return


# endregion

# region Discord application commands


async def set_command_status(command_id, status, error_msg=""):
    """Set the command status for the specified command id."""
    await db_int.set_discord_command_status(command_id, status, error_msg)
    logger.info(f"Set command [{command_id}] to {status}")
    return


async def discord_queue_callback(command: dict):
    """Handler for queued external discord commands."""

    logger.debug(f"Received discord_queue_callback with command:{command}")

    if command["object"] == "discord.TextChannel":
        # region Object Creation
        if "id" in command["attributes"]:
            channel = client.get_channel(command["attributes"]["id"])
            channel = typing.cast(discord.TextChannel, channel)
            logger.debug("Got channel object for command")
        else:
            logger.error("No id provided to send message")
            return
        # endregion

        # region Method Handling
        if command["method"] == "send":
            await channel.send(**command["args"])
            logger.info("Message sent to channel")
            await set_command_status(command["command_id"], "SUCC")
            return
        # endregion

    else:
        logger.warning("Object type %s not supported. Ignoring command" % command["object"])
        return

# endregion


client.run(credentials["bot_token"])
