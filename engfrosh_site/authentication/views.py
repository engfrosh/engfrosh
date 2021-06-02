from django.shortcuts import render  # noqa F401
from django.shortcuts import redirect
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from .discord_auth import register

from django.conf import settings

import os
import sys

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)

# Hack for development to get around import issues
sys.path.append(PARENT_DIRECTORY)
from engfrosh_common.DiscordAPI import build_oauth_authorize_url # noqa E402


def index(request: HttpRequest):
    return render(request, "index.html")

# region Logins


def login_page(request: HttpRequest):
    return render(request, "login.html")


def discord_login(request: HttpRequest):
    callback_url = request.build_absolute_uri("callback/")

    return redirect(
        build_oauth_authorize_url(
            settings.DISCORD_CLIENT_ID, callback_url, settings.DEFAULT_DISCORD_SCOPE, prompt="none"))


def discord_login_callback(request: HttpRequest):

    oauth_code = request.GET.get("code")
    # oauth_state = request.GET.get("state")

    callback_url = request.build_absolute_uri(request.path)

    user = authenticate(request, discord_oauth_code=oauth_code, callback_url=callback_url)
    if user is not None:
        login(request, user, backend="authentication.discord_auth.DiscordAuthBackend")
        return redirect("discord_welcome")

    else:
        return redirect("login_failed")


def login_failed(request):
    return HttpResponse("Your login attempt failed for some reason")
# endregion


# region Registration

def register_page(request: HttpRequest):
    return render(request, "register.html")


def discord_register(request):
    callback_url = request.build_absolute_uri("callback/")

    return redirect(
        build_oauth_authorize_url(
            settings.DISCORD_CLIENT_ID, callback_url, scope=settings.DEFAULT_DISCORD_SCOPE,
            prompt="consent"))


def discord_register_callback(request: HttpRequest):
    oauth_code = request.GET.get("code")
    # oauth_state = request.GET.get("state")

    callback_url = request.build_absolute_uri(request.path)

    user = register(discord_oauth_code=oauth_code, callback_url=callback_url)
    login(request, user, backend="authentication.discord_auth.DiscordAuthBackend")

    return redirect("discord_welcome")


@login_required()
def discord_initial_setup(request: HttpRequest):
    return HttpResponse("You are logged in")
# endregion
