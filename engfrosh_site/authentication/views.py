import os
import sys

from .discord_auth import register
from . import credentials

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.utils.encoding import iri_to_uri, uri_to_iri
from django.conf import settings


CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)

# Hack for development to get around import issues
sys.path.append(PARENT_DIRECTORY)
from engfrosh_common.DiscordAPI import build_oauth_authorize_url  # noqa E402


def index(request: HttpRequest):
    return render(request, "index.html")


@login_required()
def home_page(request: HttpRequest):
    return HttpResponse(request.user.get_username())

# region Logins


def login_page(request: HttpRequest):
    if not request.user.is_anonymous:
        # Todo add way to log out
        return HttpResponse("You are already loged in.")

    redir = request.GET.get("redirect")

    if token := request.GET.get("auth"):
        user = authenticate(request, magic_link_token=token)
        if user:
            login(request, user, "authentication.discord_auth.DiscordAuthBackend")
            if redir:
                return redirect(uri_to_iri(redir))
            return redirect("home")

    context = {}
    if redir:
        context["encoded_redirect"] = redir

    # Todo handle the redirect url on the other end
    return render(request, "login.html", context)


def discord_login(request: HttpRequest):
    callback_url = request.build_absolute_uri("callback/")

    return redirect(
        build_oauth_authorize_url(
            credentials.DISCORD_CLIENT_ID, callback_url, settings.DEFAULT_DISCORD_SCOPE, prompt="none"))


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
    return render(request, "login_failed.html")
# endregion


def permission_denied(request: HttpRequest):
    return render(request, "permission_denied.html")


@login_required()
def link_discord(request: HttpRequest):
    skip_confirmation = request.GET.get("skip-confirm")
    if skip_confirmation and skip_confirmation == "true":
        return redirect("discord_register")

    return render(request, "link_discord.html")


# region Registration

def register_page(request: HttpRequest):
    return render(request, "register.html")


def discord_register(request):
    callback_url = request.build_absolute_uri("callback/")

    return redirect(
        build_oauth_authorize_url(
            credentials.DISCORD_CLIENT_ID, callback_url, scope=settings.DEFAULT_DISCORD_SCOPE,
            prompt="consent"))


def discord_register_callback(request: HttpRequest):
    oauth_code = request.GET.get("code")
    # oauth_state = request.GET.get("state")

    user = request.user
    if user.is_anonymous:
        user = None

    callback_url = request.build_absolute_uri(request.path)

    user = register(discord_oauth_code=oauth_code, callback_url=callback_url, user=user)
    login(request, user, backend="authentication.discord_auth.DiscordAuthBackend")

    return redirect("discord_welcome")


@login_required()
def discord_initial_setup(request: HttpRequest):
    return HttpResponse("You are logged in")
# endregion
