import discord
import sys

import logging
import os

import json

import threading

import psycopg2
import asyncio

USE_RABBIT = False
USE_POSTGRES = False

if USE_RABBIT:
    from . import rabbit_listener


CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)

# Hack for development to get around import issues
sys.path.append(PARENT_DIRECTORY)

LOG_LEVEL = logging.DEBUG

RABBIT_HOST = "localhost"
QUEUE = "django_discord"

# region Logging Setup
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]

logger = logging.getLogger(SCRIPT_NAME)

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

logger.debug("Set current directory as: %s", CURRENT_DIRECTORY)
# endregion


# region Load Settings
with open(CURRENT_DIRECTORY + "/credentials.json") as f:
    bot_token = json.load(f)["bot_token"]
# endregion

client = discord.Client()
# TODO Change this to a discord bot instead of client

# region Discord Events


@client.event
async def on_ready():
    logger.info("Successfully Logged In")

    # region Launch Queue Listener
    # You shouldn't have to change anything in here.
    # To add more functions add them to handle_queued_command
    if USE_RABBIT:
        discord_loop = asyncio.get_running_loop()
        rabbit_thread = threading.Thread(target=rabbit_listener.rabbit_main,
                                         args=(discord_loop, discord_queue_callback, RABBIT_HOST, QUEUE))
        rabbit_thread.start()
    if USE_POSTGRES:
        global sql_connection
        sql_connection = psycopg2.connect(database="engfrosh", user="discord_engfrosh",
                                          password="there-exercise-fenegel", host="localhost", port="5432")
        sql_connection.set_session(autocommit=True)
    # endregion

    return


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await message.channel.send("Hello There")
    return
# endregion

# region Discord application commands


def set_command_status(command_id, status, error_msg=""):
    cursor = sql_connection.cursor()
    cursor.execute(
        f"UPDATE discord_client_discordcommandstatus SET status = '{status}' WHERE command_id = '{command_id}'")
    # command_obj = DiscordCommandStatus.objects.filter(command_id = uuid.UUID(command_id))
    # command_obj.status = status
    # command_obj.error_message = error_msg
    return

@client.command(pass_context=True) #this command is temporary, to keep the functionality of how to react to a message easy and here.
async def react(ctx):
    await ctx.message.add_reaction("🍋")
    await ctx.channel.send("did it work?")

async def discord_queue_callback(command: dict):
    if command["object"] == "discord.TextChannel":
        # command.pop("object")
        # region Object Creation
        if "id" in command["attributes"]:
            channel = client.get_channel(command["attributes"]["id"])
            # command.pop("attributes")
        else:
            logger.error("No id provided to send message")
            return
        # endregion

        # region Method Handling
        if command["method"] == "send":
            await channel.send(**command["args"])
            set_command_status(command["command_id"], "SUCC")
            return
        # endregion

    else:
        logger.warning("Object type %s not supported. Ignoring command" % command["object"])
        return


# region program start
discord_thread = threading.Thread(target=client.run, args=(bot_token,))

discord_thread.start()
discord_thread.join()
# endregion
