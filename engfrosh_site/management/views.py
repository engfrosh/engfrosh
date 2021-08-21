"""Views for management pages."""

import logging
import requests
import json
import os

import credentials

from engfrosh_common.DiscordAPI.DiscordAPI import DiscordAPI
from engfrosh_common.DiscordAPI.DiscordUserAPI import DiscordUserAPI
from authentication.models import DiscordUser
from frosh.models import FroshRole, Team
import scavenger.models
import discord_bot_manager.models
from discord_bot_manager.models import Role
from . import registration

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse, HttpResponseBadRequest, \
    HttpResponseNotAllowed, HttpResponseServerError
from django.shortcuts import render


logger = logging.getLogger("management.views")

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)


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
            if not usr.is_superuser:
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
            return HttpResponseBadRequest("Invalid command")

    return HttpResponseServerError()

# TODO Limit access to staff


def manage_index(request: HttpRequest) -> HttpResponse:
    """Home page for management."""
    return render(request, "manage.html")


@permission_required("frosh_team.change_team")
def manage_frosh_teams(request: HttpRequest) -> HttpResponse:
    """Page to manage and add frosh teams."""
    if request.method == "GET":
        context = {"teams": []}
        for team in Team.objects.all():
            if Role.objects.filter(group_id=team.group).exists():
                role_exists = True
            else:
                role_exists = False

            try:
                scav_team = scavenger.models.Team.objects.get(group=team.group)
            except ObjectDoesNotExist:
                scav_channel = None
                logger.warning(f"No scav team exists for team: {team}")
            else:
                try:
                    scav_channel = discord_bot_manager.models.ScavChannel.objects.get(group=team.group).channel_id
                except ObjectDoesNotExist:
                    logger.info(f"No scav channel exists for team: {team}")
                    scav_channel = None

            team_color = team.color_code

            t = {
                "id": team.group.id,
                "name": team.display_name,
                "discord_role": role_exists,
                "color": team_color if team_color else None,
                "scav_channel": scav_channel
            }
            context["teams"].append(t)
        return render(request, "frosh_teams.html", context)

    if request.method == "POST":
        if request.content_type != "application/json":
            return HttpResponseBadRequest("Invalid / missing content type.")

        req_dict = json.loads(request.body)
        if "command" not in req_dict:
            return HttpResponseBadRequest("Bad request body.")

        # ADD DISCORD ROLE TO A TEAM
        if req_dict["command"] == "add_discord_role":
            if "team_id" not in req_dict:
                return HttpResponseBadRequest("No team id.")
            try:
                group = Group.objects.get(id=req_dict["team_id"])
                team = Team.objects.get(group=group)
            except ObjectDoesNotExist:
                return HttpResponseBadRequest("Invalid team id")

            discord_api = DiscordAPI(credentials.BOT_TOKEN, api_version=settings.DEFAULT_DISCORD_API_VERSION)

            try:
                role_id = discord_api.create_guild_role(credentials.GUILD_ID, name=team.display_name, color=team.color)
            except requests.HTTPError as e:
                logger.error(f"HTTP Error. \nRequest: {e.request} \nResponse: {e.response}")
                return HttpResponseServerError("Could not add guild role.")

            role = Role(role_id=role_id, group_id=group)
            role.save()

            return JsonResponse({"team_id": group.id, "role_id": role.role_id})  # type: ignore

        # CREATE A NEW TEAM
        elif req_dict["command"] == "add_team":
            if "team_name" not in req_dict or not req_dict["team_name"]:
                return HttpResponseBadRequest("No team name provided.")
            team_name = req_dict["team_name"]

            group = Group(name=team_name)
            group.save()

            if "team_color" in req_dict and req_dict["team_color"]:
                team_color = req_dict["team_color"]
            else:
                team_color = None

            team = Team(display_name=team_name, group=group, color=team_color)
            team.save()

            scav_team = scavenger.models.Team(group=group)
            scav_team.reset_progress()
            scav_team.save()

            return JsonResponse(team.to_dict())

        # UPDATE AN EXISTING TEAM
        elif req_dict["command"] == "update_team":
            if "team_id" not in req_dict:
                return HttpResponseBadRequest("No team id.")

            try:
                group = Group.objects.get(id=req_dict["team_id"])
                team = Team.objects.get(group=group)
            except ObjectDoesNotExist:
                return HttpResponseBadRequest("Invalid team id")

            logger.debug(f"Request: {req_dict}")

            if "team_color" in req_dict and isinstance(req_dict["team_color"], int):
                logger.debug(f"Setting team color to : {req_dict['team_color']}")
                team.color = req_dict["team_color"]
                team.save()

            return JsonResponse(team.to_dict())

        else:
            return HttpResponseBadRequest("Invalid command.")

    return HttpResponseBadRequest()
