"""Views for custom authentication.

Includes views for:
 - login
 - registration
 - custom user management.
"""

import os
import sys
import json

from django.contrib.auth.models import User
from django.http.response import HttpResponseBadRequest, HttpResponseNotAllowed, \
    HttpResponseServerError, JsonResponse

from .discord_auth import register
from . import credentials
from . import registration

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.encoding import uri_to_iri
from django.conf import settings


CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)

# Hack for development to get around import issues
sys.path.append(PARENT_DIRECTORY)
from engfrosh_common.DiscordAPI import build_oauth_authorize_url  # noqa E402


def index(request: HttpRequest):
    """Generic accounts home."""
    return render(request, "index.html")


@login_required()
def home_page(request: HttpRequest):
    """Home page for users. Currently just prints username for debugging."""
    return HttpResponse(request.user.get_username())


@permission_required("auth_user.change_user")
def get_discord_link(request: HttpRequest) -> HttpResponse:
    """View to get discord linking links for users."""
    if request.method == "GET":
        # Handle Webpage requests
        context = {"users": []}

        users = User.objects.all()
        for usr in users:
            if not usr.is_staff:
                context["users"].append(usr)

        return render(request, "create_discord_magic_links.html", context)

    elif request.method == "POST":
        # Handle commands
        if request.content_type != "application/json":
            return HttpResponseBadRequest()

        req_dict = json.loads(request.body)
        if "user_id" not in req_dict:
            return HttpResponseBadRequest()

        user = User.objects.get(id=req_dict["user_id"])

        link = registration.get_magic_link(
            user, request.get_host(),
            "/accounts/login", redirect="/accounts/link/discord")
        if not link:
            return HttpResponseServerError()

        return JsonResponse({"user_id": user.id, "link": link})

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])


# region Logins


def login_page(request: HttpRequest):
    """Login page. Currently just links to login with discord."""
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
    """Redirects user to discord authentication to log in."""
    callback_url = request.build_absolute_uri("callback/")

    return redirect(
        build_oauth_authorize_url(
            credentials.DISCORD_CLIENT_ID, callback_url, settings.DEFAULT_DISCORD_SCOPE, prompt="none"))


def discord_login_callback(request: HttpRequest):
    """Callback view that handles post discord login authentication.

    On success: redirects to home
    On failure: redirects to permission denied
    """

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
    """View for login failed."""
    return render(request, "login_failed.html")
# endregion


def permission_denied(request: HttpRequest):
    """View for permission denied."""
    return render(request, "permission_denied.html")


@login_required()
def link_discord(request: HttpRequest):
    """Page to prompt user to link their discord account to their user account."""
    skip_confirmation = request.GET.get("skip-confirm")
    if skip_confirmation and skip_confirmation == "true":
        return redirect("discord_register")

    return render(request, "link_discord.html")


# region Registration

def register_page(request: HttpRequest):
    """Generic registration page, links to register with discord page."""
    return render(request, "register.html")


def discord_register(request):
    """Redirects to discord authentication to register."""
    callback_url = request.build_absolute_uri("callback/")

    return redirect(
        build_oauth_authorize_url(
            credentials.DISCORD_CLIENT_ID, callback_url, scope=settings.DEFAULT_DISCORD_SCOPE,
            prompt="consent"))


def discord_register_callback(request: HttpRequest):
    """
    Callback for post discord authentication, creates a discord user account.

    If the user is logged in it will link their user account to the new discord account.
    If not it will create a new user account.
    """
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
    """Redirect for after user has registered with discord account."""
    return HttpResponse("You are logged in")
# endregion
