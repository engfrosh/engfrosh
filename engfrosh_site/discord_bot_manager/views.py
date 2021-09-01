from django.shortcuts import render  # noqa F401

from django.http import HttpResponse
import datetime
import os

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(os.path.dirname(CURRENT_DIRECTORY))


from engfrosh_common.RabbitMQSender import RabbitMQSender  # noqa E402
from . import discord_publisher  # noqa E402

RABBIT_HOST = "localhost"
RABBIT_DISCORD_QUEUE = "django_discord"


def index(request):
    time = datetime.datetime.now().isoformat()
    message = f"Hello, it is {time}"
    sender = RabbitMQSender(RABBIT_DISCORD_QUEUE, RABBIT_HOST)
    channel = discord_publisher.TextChannel(sender, 731598642426675305)
    command_id = channel.send(message)
    response = f"Message Sent: {message}\nMessage Status: {discord_publisher.check_command_status(command_id)[0]}"
    return HttpResponse(response)
