# Discord Authentication Details for OAuth Application
# This needs to be the same application as the bot in the server

import os
import logging

DISCORD_CLIENT_ID = r""
DISCORD_CLIENT_SECRET = r""
GUILD_ID = 0
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not BOT_TOKEN:
    logging.warning("No discord bot token provided")
