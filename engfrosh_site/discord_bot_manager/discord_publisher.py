import logging
# import uuid
import datetime
# import dateutil

import os

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)


from engfrosh_common import RabbitMQSender  # noqa E402

from discord_bot_manager.models import DiscordCommandStatus  # noqa E402

logger = logging.getLogger("DiscordPublisher")


class DiscordPublisher():
    def __init__(self, sender: RabbitMQSender.RabbitMQSender):
        self.sender = sender

    def _send_message(self, message_dict):
        message_dict["command_id"] = self._add_command_status()
        self.sender.send(message_dict)
        return message_dict["command_id"]

    def _add_command_status(self):
        timeout = datetime.datetime.now() + datetime.timedelta(1)
        command_status = DiscordCommandStatus(status="PEND", timeout=timeout)
        command_status.save()
        return str(command_status.command_id)


class TextChannel(DiscordPublisher):
    def __init__(self, sender: RabbitMQSender.RabbitMQSender, id):
        super().__init__(sender)
        self.id = id

    def send(self, content: str):
        """Returns the command that can be checked later"""
        d = {
            "type": "discord.py",
            "object": "discord.TextChannel",
            "attributes": {"id": self.id},
            "method": "send",
            "args": {
                "content": content
                # "embed": ,
                # "file":
                # "files":
                # "delete_after":
                # "allowed_mentions":
                # "reference":
                # "mention_author":
            }
        }
        return self._send_message(d)


def check_command_status(command_id: str):
    return DiscordCommandStatus.objects.get(command_id=command_id).get_status()
