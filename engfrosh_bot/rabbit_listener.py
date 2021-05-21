import logging
import os

import asyncio
import functools

import json

import pika

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


def handle_queued_command(ch, method, properties, body, args):
    discord_loop, discord_queue_callback = args

    message = json.loads(body)
    if type(message) != dict:
        logger.error(f"Message not dict. Ignored: {message}")
    elif message["type"] != "discord.py":
        logger.warning(f"Message not discord message. Ignored: {message}")
    else:
        message.pop("type")
        asyncio.run_coroutine_threadsafe(
            discord_queue_callback(message), discord_loop)
    return


def rabbit_main(discord_loop, discord_queue_callback, host, queue):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host))
    rabbit_channel = connection.channel()

    rabbit_channel.queue_declare(queue=queue)
    handle_queued_command_callback = functools.partial(
        handle_queued_command, args=(discord_loop, discord_queue_callback))

    rabbit_channel.basic_consume(queue=queue, auto_ack=True,
                                 on_message_callback=handle_queued_command_callback)

    rabbit_channel.start_consuming()
