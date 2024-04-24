"""Views for custom authentication.

Includes views for:
 - login
 - registration
 - custom user management.
"""

import logging
import os
from typing import List, Union
from urllib.parse import urlparse
import credentials
import uuid

from common_models.models import DiscordUser
from common_models.models import DiscordRole, Setting
from .discord_auth import DiscordUserAlreadyExistsError, register
from pyaccord.DiscordUserAPI import DiscordUserAPI, build_oauth_authorize_url  # noqa E402

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.http import HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.encoding import uri_to_iri
from django.conf import settings
from django.contrib.auth.models import User

import msal

logger = logging.getLogger("Authentication.Views")

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)


def index(request: HttpRequest):
    """Generic accounts home."""
    return render(request, "index.html")


def msLogin(request: HttpRequest):
    AUTHORITY = "https://login.microsoftonline.com/common"
    app = msal.ConfidentialClientApplication(settings.MICROSOFT_ID, authority=AUTHORITY,
                                             client_credential=settings.MICROSOFT_TOKEN)
    base_url = Setting.objects.get_or_create(id="callback_base",
                                             defaults={"value": "https://server.engfrosh.com"})[0].value
    callback_url = base_url + "/accounts/msTokenCallback"
    SCOPE = []
    url = app.get_authorization_request_url(SCOPE, state=str(uuid.uuid4()), redirect_uri=callback_url)
    return redirect(url)


def msTokenCallback(request: HttpRequest):
    if request.user.is_authenticated:
        logout(request)
    params = request.GET
    if 'code' not in params or 'state' not in params or 'session_state' not in params:
        return HttpResponseBadRequest("Missing code and session state! " +
                                      "You probably are signed in using your personal Microsoft account. "
                                      "Clear your cookies and if the issue persists contact technical@engfrosh.com")
    code = params['code']
    # state = params['state']
    # session_state = params['session_state']
    AUTHORITY = "https://login.microsoftonline.com/common"
    app = msal.ConfidentialClientApplication(settings.MICROSOFT_ID, authority=AUTHORITY,
                                             client_credential=settings.MICROSOFT_TOKEN)
    SCOPE = []
    base_url = Setting.objects.get_or_create(id="callback_base",
                                             defaults={"value": "https://server.engfrosh.com"})[0].value
    callback_url = base_url + "/accounts/msTokenCallback"
    token = app.acquire_token_by_authorization_code(code, SCOPE, redirect_uri=callback_url)
    if 'id_token_claims' not in token:
        return HttpResponseBadRequest("Invalid or expired code!")
    email = token['id_token_claims']['preferred_username'].lower()
    user = User.objects.filter(email=email).first()
    if user is None:
        logger.error("Email is not registered: " + email)
        return HttpResponse("Email is not registered!" +
                            "You must sign in with the email you supplied on your application!")
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    discord = DiscordUser.objects.filter(user=user).first()
    if discord is None:
        return redirect("link_discord")
    home_url = Setting.objects.get_or_create(id="home_url",
                                             defaults={"value": "https://time.engfrosh.com/user/"})[0].value
    return redirect(home_url)


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
            is_absolute = bool(urlparse(redirect_location).netloc)
            if is_absolute:
                return HttpResponse("Warning: Absolute redirect url detected!")
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
    base_url = Setting.objects.get_or_create(id="callback_base",
                                             defaults={"value": "https://server.engfrosh.com"})[0].value
    callback_url = base_url + "/accounts/login/discord/callback/"
    # TODO add redirect for the next page here

    return redirect(
        build_oauth_authorize_url(
            credentials.DISCORD_CLIENT_ID, callback_url, settings.DEFAULT_DISCORD_SCOPE, prompt="none"))


def username_login(request: HttpRequest):
    if request.method == "POST":
        if 'username' not in request.POST or 'password' not in request.POST:
            return redirect("login_failed")
            pass
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            login(request, user,
                  backend="authentication.loginbackend.EmailOrUsernameAuthenticationBackend")
            return redirect("user_home")
        else:
            return redirect("login_failed")
    else:
        return render(request, "username_login.html", {})


def discord_login_callback(request: HttpRequest):
    """Callback view that handles post discord login authentication.

    On success: redirects to home
    On failure: redirects to permission denied
    """

    oauth_code = request.GET.get("code")

    if request.GET.get("error", "") == "access_denied":
        return redirect("login_failed")
    # oauth_state = request.GET.get("state")
    base_url = Setting.objects.get_or_create(id="callback_base",
                                             defaults={"value": "https://server.engfrosh.com"})[0].value
    callback_url = base_url + "/accounts/login/discord/callback/"

    user = authenticate(request, discord_oauth_code=oauth_code, callback_url=callback_url)
    if user is not None:
        login(request, user, backend="authentication.discord_auth.DiscordAuthBackend")
        home_url = Setting.objects.get_or_create(id="home_url",
                                                 defaults={"value": "https://time.engfrosh.com/user/"})[0].value
        return redirect(home_url)

    else:
        return redirect("login_failed")


def login_failed(request):
    """View for login failed."""
    return render(request, "login_failed.html", status=400)
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
    base_url = Setting.objects.get_or_create(id="callback_base",
                                             defaults={"value": "https://server.engfrosh.com"})[0].value
    callback_url = base_url + "/accounts/register/discord/callback/"

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

    base_url = Setting.objects.get_or_create(id="callback_base",
                                             defaults={"value": "https://server.engfrosh.com"})[0].value
    callback_url = base_url + "/accounts/register/discord/callback/"

    try:
        user = register(discord_oauth_code=oauth_code, callback_url=callback_url, user=user)
    except DiscordUserAlreadyExistsError:
        return HttpResponse(
            "There is already a discord account associated with your id." +
            " You may already be in the server, you can check by logging into discord directly." +
            " If not, please contact the administrator.")

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
                    query = DiscordRole.objects.filter(group_id=g)
                    for role in query:
                        if role.secondary_group is None or role.secondary_group in groups:
                            discord_role_ids.append(role.role_id)
                except ObjectDoesNotExist:
                    continue

            if not discord_role_ids:
                discord_role_ids = None

            if user_api.add_user_to_guild(credentials.GUILD_ID, user_id=discord_user.id,
                                          roles=discord_role_ids, nickname=user.get_full_name()):
                logger.info(f"Successfully added user {discord_user} to discord server.")

            else:
                logger.warning(f"Failed to add user {discord_user} to discord server.")
    home_url = Setting.objects.get_or_create(id="home_url",
                                             defaults={"value": "https://time.engfrosh.com/user/"})[0].value
    return redirect(home_url)


@login_required()
def discord_initial_setup(request: HttpRequest):
    """Redirect for after user has registered with discord account."""
    context = {"guild_id": credentials.GUILD_ID}
    # TODO add the welcome channel id here.
    # context = {"guild_id": credentials.GUILD_ID, "channel_id": channel_id}
    return render(request, "discord_welcome.html", context)
# endregion
