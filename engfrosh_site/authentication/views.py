"""Views for custom authentication.

Includes views for:
 - login
 - registration
 - custom user management.
"""

import logging
import os
from typing import List, Union

import credentials

from common_models.models import DiscordUser
from common_models.models import DiscordRole
from .discord_auth import DiscordUserAlreadyExistsError, register
from pyaccord.DiscordUserAPI import DiscordUserAPI, build_oauth_authorize_url  # noqa E402

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.encoding import uri_to_iri
from django.conf import settings

logger = logging.getLogger("Authentication.Views")

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)


def index(request: HttpRequest):
    """Generic accounts home."""
    return render(request, "index.html")


@login_required()
def home_page(request: HttpRequest):
    """Home page for users. Currently just prints username for debugging."""
    return HttpResponse(request.user.get_username())


@login_required()
def link_discord(request: HttpRequest):
    """Page to prompt user to link their discord account to their user account."""
    skip_confirmation = request.GET.get("skip-confirm")
    if skip_confirmation and skip_confirmation == "true":
        return redirect("discord_register")

    return render(request, "link_discord.html")
# endregion

# region Logins


def logout_page(request: HttpRequest) -> HttpResponse:

    logout(request)

    return HttpResponse("You are now logged out.")


def login_page(request: HttpRequest):
    """Login page."""
    redirect_location = request.GET.get("redirect")
    if not redirect_location:
        redirect_location = request.GET.get("next")

    if not request.user.is_anonymous:
        # Todo add way to log out
        if redirect_location:
            return redirect(redirect_location)
        else:
            return HttpResponse("You are already logged in.")

    if token := request.GET.get("auth"):
        user = authenticate(request, magic_link_token=token)
        if user:
            login(request, user, "authentication.discord_auth.DiscordAuthBackend")
            if redirect_location:
                return redirect(uri_to_iri(redirect_location))
            return redirect("home")

    context = {}
    if redirect_location:
        context["encoded_redirect"] = redirect_location

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


# region Single User Registration

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
        # If disallowing registration to pre registered people.
        return HttpResponse("Registration failed, please contact questions@engfrosh.com")

    callback_url = request.build_absolute_uri(request.path)

    try:
        user = register(discord_oauth_code=oauth_code, callback_url=callback_url, user=user)
    except DiscordUserAlreadyExistsError:
        return HttpResponse(
            "There is already a discord account associated with your id. You may already be in the server, you can check by logging into discord directly. If not, please contact the administrator.")

    if not user:
        logger.error("Could not register user.")
        raise Exception("Could not register user.")
    login(request, user, backend="authentication.discord_auth.DiscordAuthBackend")

    if credentials.GUILD_ID:
        discord_user = DiscordUser.objects.get(user=user)
        if not discord_user:
            logger.error(f"Could not get discord user for user {user} after they registered.")

        else:
            user_api = DiscordUserAPI(bot_token=credentials.BOT_TOKEN, access_token=discord_user.access_token,
                                      refresh_token=discord_user.refresh_token, expiry=discord_user.expiry)

            # Get all the roles that the user has and their corresponding Discord Roles
            groups = user.groups.all()
            discord_role_ids: Union[List[int], None] = []
            for g in groups:
                try:
                    discord_role_ids.append(DiscordRole.objects.get(group_id=g).role_id)
                except ObjectDoesNotExist:
                    continue

            if not discord_role_ids:
                discord_role_ids = None

            if user_api.add_user_to_guild(credentials.GUILD_ID, user_id=discord_user.id,
                                          roles=discord_role_ids, nickname=user.get_full_name()):
                logger.info(f"Successfully added user {discord_user} to discord server.")

            else:
                logger.warning(f"Failed to add user {discord_user} to discord server.")

    return redirect("discord_welcome")


@login_required()
def discord_initial_setup(request: HttpRequest):
    """Redirect for after user has registered with discord account."""
    context = {"guild_id": credentials.GUILD_ID}
    # TODO add the welcome channel id here.
    # context = {"guild_id": credentials.GUILD_ID, "channel_id": channel_id}
    return render(request, "discord_welcome.html", context)
# endregion
