"""Views for management pages."""

import logging
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse, HttpResponseBadRequest, \
    HttpResponseNotAllowed, HttpResponseServerError
from django.shortcuts import render
from django.contrib.auth.models import User

from authentication.models import DiscordUser
from frosh.models import FroshRole, Team
from . import registration
import json

from engfrosh_common.DiscordUserAPI import DiscordUserAPI

import credentials

logger = logging.getLogger("management.views")


@permission_required("auth_user.add_user")
def bulk_register_users(request: HttpRequest) -> HttpResponse:
    """View for bulk user adding."""

    if request.method == "GET":
        role_options = []
        for role in FroshRole.objects.all():
            role_options.append(role.name)

        team_options = []
        for team in Team.objects.all():
            team_options.append(team.display_name)

        context = {
            "team_options": team_options,
            "role_options": role_options
        }
        return render(request, "bulk_user_add.html", context)

    elif request.method == "POST":

        if request.content_type != "application/json":
            return HttpResponseBadRequest("Not application/json content type")

        req_dict = json.loads(request.body)
        try:
            if req_dict["command"] != "add_user":
                return HttpResponseBadRequest()

            name = req_dict["name"]
            email = req_dict["email"]
            team = req_dict["team"]
            role = req_dict["role"]
        except KeyError:
            return HttpResponseBadRequest("Key Error in Body")

        try:
            role = FroshRole.objects.get(name=role)
            if team:
                team = Team.objects.get(display_name=team)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest("Bad role or team")

        try:
            user = registration.create_user_initialize(name, email, role, team)
        except registration.UserAlreadyExistsError:
            return HttpResponseBadRequest("User already exists.")

        return JsonResponse({"user_id": user.id, "username": user.username})  # type: ignore

    return HttpResponseBadRequest()


# region Link Discord


@permission_required("auth_user.change_user")
def get_discord_link(request: HttpRequest) -> HttpResponse:
    """View to get discord linking links for users or send link emails to users."""
    if request.method == "GET":
        # Handle Webpage requests
        # TODO add check that user doesn't yet have a discord account linked.
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
        if "user_id" not in req_dict and "command" not in req_dict and req_dict["command"] not in {
                "return_link", "send_link_email"}:
            return HttpResponseBadRequest()

        user = User.objects.get(id=req_dict["user_id"])

        if req_dict["command"] == "return_link":
            link = registration.get_magic_link(
                user, request.get_host(),
                "/accounts/login", redirect="/accounts/link/discord")
            if not link:
                logger.error("Could not get magic link for user %s", user)
                return HttpResponseServerError("Could not get link for user.")
            return JsonResponse({"user_id": user.id, "link": link})

        elif req_dict["command"] == "send_link_email":
            # TODO Update the email to be dynamic
            SENDER_EMAIL = "noreply@engfrosh.com"
            if registration.email_magic_link(
                    user, request.get_host(),
                    "/accounts/login", SENDER_EMAIL,
                    redirect="/accounts/link/discord"):
                # Email successfully sent
                return JsonResponse({"user_id": user.id})

            else:
                # Email failed for some reason
                return HttpResponseServerError()

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

    return HttpResponseServerError()


@permission_required("auth_user.change_user")
def add_discord_user_to_guild(request: HttpRequest) -> HttpResponse:
    """Add users to to the discord server."""

    if request.method == "GET":
        context = {
            "users": []
        }

        users = User.objects.all()
        for usr in users:
            if not usr.is_staff and DiscordUser.objects.filter(user=usr).exists():
                context["users"].append(usr)

        return render(request, "add_discord_user_to_guild.html", context)

    elif request.method == "POST":

        if request.content_type != "application/json":
            return HttpResponseBadRequest("Invalid / missing content type.")

        req_dict = json.loads(request.body)
        if "user_id" not in req_dict and "command" not in req_dict:
            return HttpResponseBadRequest("Bad request body.")

        if req_dict["command"] == "add_user":
            # Get user information
            logger.debug(f"Trying to add website user with id {req_dict['user_id']}")
            discord_user = DiscordUser.objects.get(user=req_dict["user_id"])
            if not discord_user:
                return HttpResponseBadRequest("User does not exist / have a discord account linked.")

            user_api = DiscordUserAPI(bot_token=credentials.BOT_TOKEN,
                                      access_token=discord_user.access_token, refresh_token=discord_user.refresh_token,
                                      expiry=discord_user.expiry)

            # TODO Make guild id dynamic
            res = user_api.add_user_to_guild(credentials.GUILD_ID, user_id=discord_user.id)

            if res:
                # Add succeeded
                return HttpResponse(status=204)

            else:
                # Add to guild failed
                logger.error(f"Request to add website user with id {req_dict['user_id']} failed.")
                return HttpResponseServerError()

        else:
            return HttpResponseBadRequest()

    return HttpResponseServerError()

# TODO Limit access to staff


def manage_index(request: HttpRequest) -> HttpResponse:
    """Home page for management."""
    return render(request, "manage.html")
