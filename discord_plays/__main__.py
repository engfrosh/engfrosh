"""Discord bot for turning discord commands into keyboard presses."""

import time
import typing
import pynput
from pynput.keyboard import Key
import discord
import yaml

import logging
import os

CURRENT_DIRECTORY = os.path.dirname(__file__)
LOG_LEVEL = logging.DEBUG

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

MAPPINGS = {
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
    "A": "z",
    "B": "x",
    "L": "a",
    "R": "s",
    "select": Key.backspace,
    "start": Key.enter
}

CONFIG_FILE = CURRENT_DIRECTORY + "/config.yaml"

with open(CONFIG_FILE, "r") as f:
    config = yaml.load(f, yaml.SafeLoader)

client = discord.Client()
ctrl = pynput.keyboard.Controller()


@client.event
async def on_ready():
    """Informs channel that the bot is ready."""
    channel = client.get_channel(config["channel"])
    channel = typing.cast(discord.TextChannel, channel)
    await channel.send("Up and ready to play!")


@client.event
async def on_message(message: discord.Message):
    """Translates message to key press if in the correct channel."""
    if message.author == client.user:
        return

    if message.channel.id != config["channel"]:
        return

    for key, value in MAPPINGS.items():
        if message.content.lower() in config["commands"][key]:
            ctrl.press(value)
            time.sleep(0.1)
            ctrl.release(value)
            logger.debug(f"Sent Press: {value}")
            print(value)
            return

    logger.debug(f"Bad command: {message.content}")
    await message.add_reaction("❌")
    return


client.run(config["bot_token"])
