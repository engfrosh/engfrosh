from django.shortcuts import render  # noqa F401

from django.http import HttpResponse
import os

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(os.path.dirname(CURRENT_DIRECTORY))


RABBIT_HOST = "localhost"
RABBIT_DISCORD_QUEUE = "django_discord"


def index(request):
    return HttpResponse("Discord Index")
