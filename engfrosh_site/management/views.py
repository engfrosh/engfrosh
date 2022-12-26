"""Views for management pages."""

import logging
from typing import List, Union
import requests
import json
import os

import credentials
import pyaccord

from pyaccord.DiscordUserAPI import DiscordUserAPI
from common_models.models import DiscordGuild, DiscordUser, MagicLink, Puzzle, TeamPuzzleActivity, VerificationPhoto
from common_models.models import FroshRole, Team, UniversityProgram, UserDetails, TeamTradeUpActivity
import common_models.models
from common_models.models import ChannelTag, DiscordChannel, DiscordRole
from pyaccord.invite import Invite
from pyaccord.permissions import Permissions
from . import registration

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseForbidden, JsonResponse, \
    HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseServerError
from django.shortcuts import render, redirect
from django.contrib import auth


logger = logging.getLogger("management.views")

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)


@permission_required("auth.add_user")
def bulk_register_users(request: HttpRequest) -> HttpResponse:
    """View for bulk user adding."""

    if request.method == "GET":
        role_options = []

        DEFAULT_ROLES = ("Frosh", "Facil", "Head", "Planning")
        for role in DEFAULT_ROLES:
            if not FroshRole.objects.filter(name=role).exists():
                group = Group(name=role)
                group.save()
                fr = FroshRole(name=role, group=group)
                fr.save()

        for role in FroshRole.objects.all():
            role_options.append(role.name)

        team_options = []
        for team in Team.objects.all():
            team_options.append(team.display_name)

        program_options = []
        for program in UniversityProgram.objects.all():
            program_options.append(program.name)

        context = {
            "team_options": team_options,
            "role_options": role_options,
            "program_options": program_options
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
            program = req_dict["program"]
        except KeyError:
            return HttpResponseBadRequest("Key Error in Body")

        try:
            role = FroshRole.objects.get(name=role)
            if team:
                team = Team.objects.get(display_name=team)
            if program:
                program = UniversityProgram.objects.get(name=program)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest("Bad role or team")

        try:
            user = registration.create_user_initialize(name, email, role, team, program)
        except registration.UserAlreadyExistsError:
            return HttpResponseBadRequest("User already exists.")

        return JsonResponse({"user_id": user.id, "username": user.username})  # type: ignore

    return HttpResponseBadRequest()


# region Link Discord


@permission_required("auth.change_user", login_url='/accounts/login')
def get_discord_link(request: HttpRequest) -> HttpResponse:
    """View to get discord linking links for users or send link emails to users."""

    # TODO add so heads can access for their teams

    if request.method == "GET":
        # Handle Webpage requests
        # TODO add check that user doesn't yet have a discord account linked.

        context = {"users": []}

        users = User.objects.all().order_by("username")
        for usr in users:
            try:
                email_sent = UserDetails.objects.get(user=usr).invite_email_sent
            except ObjectDoesNotExist:
                email_sent = False

            if not usr.is_superuser and not DiscordUser.objects.filter(user=usr).exists():
                context["users"].append({
                    "username": usr.username,
                    "id": usr.id,
                    "email_sent": bool(email_sent)
                })

        return render(request, "create_discord_magic_links.html", context)

    elif request.method == "POST":
        # Handle commands
        if request.content_type != "application/json":
            return HttpResponseBadRequest()

        req_dict = json.loads(request.body)

        if "command" not in req_dict:
            return HttpResponseBadRequest("Missing command")

        if "user_id" not in req_dict:
            return HttpResponseBadRequest("Missing user_id")

        user = User.objects.get(id=req_dict["user_id"])

        match req_dict["command"]:

            # TODO should first sync and eliminate expired links

            case "return_new_link":
                link = registration.get_magic_link(
                    user, request.get_host(),
                    "/accounts/login", redirect="/accounts/link/discord")
                if not link:
                    logger.error("Could not get magic link for user %s", user)
                    return HttpResponseServerError("Could not get link for user.")
                return JsonResponse({"user_id": user.id, "link": link})  # TODO fix to include https://

            case "return_existing_link":
                try:
                    mlink = MagicLink.objects.get(user=user)
                except MagicLink.DoesNotExist:
                    link = registration.get_magic_link(
                        user, request.get_host(),
                        "/accounts/login", redirect="/accounts/link/discord")
                    if not link:
                        logger.error("Could not get magic link for user %s", user)
                        return HttpResponseServerError("Could not get link for user.")
                    return JsonResponse({"user_id": user.id, "link": link})  # TODO fix to include https://

                return JsonResponse(
                    {"user_id": user.id, "link": mlink.full_link(
                        hostname=request.get_host(),
                        login_path="/accounts/login", redirect="/accounts/link/discord")})  # TODO fix to include https://

            case "send_link_email":
                # TODO Update the email to be dynamic
                SENDER_EMAIL = "noreply@engfrosh.com"
                if registration.email_magic_link(
                        user, request.get_host(),
                        "/accounts/login", SENDER_EMAIL,
                        redirect="/accounts/link/discord",
                        delete_on_use=False):
                    # Email successfully sent
                    return JsonResponse({"user_id": user.id})

                else:
                    # Email failed for some reason
                    return HttpResponseServerError()

            case "return_qr_code":
                try:
                    mlink = MagicLink.objects.get(user=user)
                except MagicLink.DoesNotExist:
                    link = registration.get_magic_link(
                        user, request.get_host(),
                        "/accounts/login", redirect="/accounts/link/discord")
                    if not link:
                        logger.error("Could not get magic link for user %s", user)
                        return HttpResponseServerError("Could not get link for user.")
                    mlink = MagicLink.objects.get(user=user)

                mlink._generate_qr_code(
                    hostname=request.get_host(),
                    login_path="/accounts/login", redirect="/accounts/link/discord")

                return JsonResponse(
                    {"user_id": user.id, "qr_code_link": mlink.qr_code.url})

            case _:
                return HttpResponseBadRequest(f"Invalid command: {req_dict['command']}")

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

# endregion


@permission_required("auth.change_user")
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
            user = User.objects.get(id=req_dict["user_id"])
            if not discord_user:
                return HttpResponseBadRequest("User does not exist / have a discord account linked.")

            user_api = DiscordUserAPI(bot_token=credentials.BOT_TOKEN,
                                      access_token=discord_user.access_token, refresh_token=discord_user.refresh_token,
                                      expiry=discord_user.expiry)

            groups = user.groups.all()
            discord_role_ids: Union[List[int], None] = []
            for g in groups:
                try:
                    discord_role_ids.append(DiscordRole.objects.get(group_id=g).role_id)
                except ObjectDoesNotExist:
                    continue

            if not discord_role_ids:
                discord_role_ids = None

            # TODO Make guild id dynamic
            res = user_api.add_user_to_guild(credentials.GUILD_ID, user_id=discord_user.id,
                                             roles=discord_role_ids, nickname=user.get_full_name())

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


@staff_member_required(login_url='/accounts/login')
def manage_index(request: HttpRequest) -> HttpResponse:
    """Home page for management."""
    return render(request, "manage.html")


@staff_member_required(login_url='/accounts/login')
def initialize_database(request: HttpRequest) -> HttpResponse:
    common_models.models.initialize_database()
    return redirect("manage_index")
@staff_member_required(login_url='/accounts/login')
def initialize_scav(request: HttpRequest) -> HttpResponse:
    common_models.models.initialize_scav()
    return redirect("manage_index")

@permission_required("frosh_team.change_team")
def manage_frosh_teams(request: HttpRequest) -> HttpResponse:
    """Page to manage and add frosh teams."""
    if request.method == "GET":
        context = {"teams": []}
        for team in Team.objects.all():
            if DiscordRole.objects.filter(group_id=team.group).exists():
                role_exists = True
            else:
                role_exists = False

            try:
                scav_team = common_models.models.Team.objects.get(group=team.group)
            except ObjectDoesNotExist:
                scav_channel = None
                logger.warning(f"No scav team exists for team: {team}")
            else:
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

            discord_api = pyaccord.Client(credentials.BOT_TOKEN, api_version=settings.DEFAULT_DISCORD_API_VERSION)

            try:
                role = discord_api.create_guild_role(credentials.GUILD_ID, name=team.display_name, color=team.color)
            except requests.HTTPError as e:
                logger.error(f"HTTP Error. \nRequest: {e.request} \nResponse: {e.response.text}")
                return HttpResponseServerError("Could not add guild role.")

            role = DiscordRole(role_id=role.id, group_id=group)
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

            # scav_team = common_models.models.Team(group=group)
            # TODO: need to fix this method
            team.reset_scavenger_progress()
            team.save()

            return JsonResponse(team.to_dict)

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

            return JsonResponse(team.to_dict)

        else:
            return HttpResponseBadRequest("Invalid command.")

    return HttpResponseBadRequest()

@permission_required("common_models.view_puzzle")
def manage_scavenger_puzzles(request: HttpRequest) -> HttpResponse:
    """Page for managing scavenger puzzles."""

    if request.method == "GET":

        for puz in Puzzle.objects.all():
            if not puz.qr_code:
                puz._generate_qr_code()

        context = {
            "puzzles": Puzzle.objects.all().order_by("order")
        }

        return render(request, "manage_scavenger_puzzles.html", context)

    elif request.method == "POST":

        return HttpResponse("Not Implemented")

        if request.content_type != "application/json":
            return HttpResponseBadRequest("Invalid / missing content type.")

        req_dict = json.loads(request.body)
        if "command" not in req_dict:
            return HttpResponseBadRequest("Bad request body, missing command.")

        # match req_dict["command"]:
        #     case "get_qr_code"

    else:
        return HttpResponseNotAllowed(("GET", "POST"))


@permission_required("common_models.change_puzzle", login_url='/accounts/login')
def approve_scavenger_puzzles(request: HttpRequest) -> HttpResponse:
    """Page for approving verification images."""

    if request.method == "GET":

        context = {"puzzle_activities_awaiting_verification": list(
            filter(TeamPuzzleActivity._is_awaiting_verification, TeamPuzzleActivity.objects.all()))}

        return render(request, "approve_scavenger_puzzles.html", context)

    elif request.method == "POST":

        if request.content_type != "application/json":
            return HttpResponseBadRequest("Invalid / missing content type.")

        req_dict = json.loads(request.body)
        if "command" not in req_dict:
            return HttpResponseBadRequest("Bad request body, missing command.")

        match req_dict["command"]:

            case "approve_verification_photo":

                if "photo_id" not in req_dict:
                    return HttpResponseBadRequest("No photo_id provided.")

                photo_id = req_dict["photo_id"]
                try:
                    photo = VerificationPhoto.objects.get(id=photo_id)
                except VerificationPhoto.DoesNotExist:
                    return HttpResponseBadRequest("Invalid photo id.")

                photo.approve()
                return HttpResponse("Success")

            case _:
                return HttpResponseBadRequest("Invalid command.")

    else:
        return HttpResponseNotAllowed(("GET", "POST"))


@permission_required("common_models.view_team")
def trade_up_viewer(request: HttpRequest) -> HttpResponse:

    context = {
        "teams": []
    }

    for team in Team.objects.all():

        items = []
        for item in TeamTradeUpActivity.objects.filter(team=team).order_by("entered_at"):
            items.append({
                "time": item.entered_at,
                "name": item.object_name,
                "photo": item.verification_photo
            })

        context["teams"].append({
            "name": team.display_name,
            "items": items
        })

    return render(request, "trade_up_viewer.html", context)
