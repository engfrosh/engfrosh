"""Views for management pages."""

import logging
from typing import List, Union
import requests
import json
import os
import datetime

import credentials

from django.contrib import auth
import pyaccord
from pyaccord.DiscordUserAPI import DiscordUserAPI
from common_models.models import DiscordChannel, DiscordUser, MagicLink, Puzzle, TeamPuzzleActivity, VerificationPhoto
from common_models.models import FroshRole, Team, UniversityProgram, UserDetails, TeamTradeUpActivity
from common_models.models import ChannelTag, DiscordGuild, Announcement, FacilShift, FacilShiftSignup
import common_models.models
from common_models.models import DiscordRole
from . import registration
from . import forms

from django.utils.html import escape
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse, \
    HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseServerError, HttpResponseForbidden
from django.shortcuts import render, redirect
from .forms import AnnouncementForm
from django.contrib.auth.decorators import user_passes_test
from management.email import send_email

from schedule.models import Event


logger = logging.getLogger("management.views")

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)


@permission_required("common_models.facil_signup")
def facil_shifts(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        shifts = list(FacilShift.objects.all())
        for shift in shifts:
            signups = len(FacilShiftSignup.objects.filter(shift=shift))
            if signups >= shift.max_facils:
                shifts.remove(shift)
            if len(FacilShiftSignup.objects.filter(shift=shift, user=request.user)) > 0:
                shifts.remove(shift)
        return render(request, "facil_shift_signup.html", {"shifts": shifts})
    elif request.method == "POST":
        shift_id = int(request.POST["shift_id"])
        shift = FacilShift.objects.filter(id=shift_id).first()
        shifts = list(FacilShift.objects.all())
        for shift in shifts:
            signups = len(FacilShiftSignup.objects.filter(shift=shift))
            if signups >= shift.max_facils:
                shifts.remove(shift)
            if len(FacilShiftSignup.objects.filter(shift=shift, user=request.user)) > 0:
                shifts.remove(shift)
        if shift is None:
            return render(request, "facil_shift_signup.html", {"shifts": shifts, "success": False})
        count = len(FacilShiftSignup.objects.filter(shift=shift))
        if count >= shift.max_facils:
            return render(request, "facil_shift_signup.html", {"shifts": shifts, "success": False})
        signup = FacilShiftSignup(user=request.user, shift=shift)
        signup.save()
        body_text = """Hello there,
        You have successfully signed up for a facil shift from {start} to {end}.
        If this is incorrect or you encounter any issues you can send an email to questions@engfrosh.com.
        """
        send_email(user=request.user, sender_email="noreply@engfrosh.com", subject="Facil Shift Signup",
                   body_text=body_text.format(start=str(shift.start), end=str(shift.end)),
                   body_html=body_text.format(start=str(shift.start), end=str(shift.end)))
        return render(request, "facil_shift_signup.html", {"shifts": shifts, "success": True})


@staff_member_required(login_url='/accounts/login')
def announcements(request: HttpRequest) -> HttpResponse:
    """View for creating announcements"""
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        context = {"form": form}
        if form.is_valid():
            data = form.cleaned_data
            announcement = Announcement(title=data['title'], body=data['body'])
            announcement.save()
            context['success'] = True
        else:
            context['error'] = True
    else:
        form = AnnouncementForm()
        context = {"form": form}
    return render(request, "announcements.html", context)


@permission_required("common_models.manage_scav")
def lock_team(request: HttpRequest, id: int) -> HttpResponse:
    if request.method == "GET":
        if id == 0:
            return render(request, "lock_teams.html", {"teams": Team.objects.all()})
        else:
            form = forms.LockForm()
            form.duration = 15

            team = Team.objects.filter(group_id=id).first()
            return render(request, "lock_team.html", {"team": team, "form": form})
    elif request.method == "POST":
        team = Team.objects.filter(group_id=id).first()
        form = forms.LockForm(request.POST)
        if not form.is_valid():
            return render(request, "lock_team.html", {"team": team, "form": form, "error": True})
        curr = datetime.datetime.now()
        delta = datetime.timedelta(minutes=form.cleaned_data['duration'])
        team.scavenger_locked_out_until = curr + delta
        team.save()
        return redirect("/manage/lock_team/0")


@permission_required("common_models.manage_scav")
def unlock_team(request: HttpRequest, id: int) -> HttpResponse:
    if id == 0:
        return render(request, "unlock_teams.html", {"teams": Team.objects.all()})
    else:
        team = Team.objects.filter(group_id=id).first()
        team.scavenger_locked_out_until = None
        team.save()
        return redirect("/manage/unlock_team/0")


@permission_required("auth.change_user")
def edit_event(request: HttpRequest, id: int) -> HttpResponse:
    if request.method == "GET":
        context = {"form": forms.EventForm(instance=Event.objects.filter(id=id).first())}
        return render(request, "edit_event.html", context)
    elif request.method == "POST":
        action = request.POST['action']
        if action == "delete":
            event = Event.objects.filter(id=id).first()
            if event is not None:
                event.delete()
            return redirect("/")
        elif action == "modify":
            form = forms.EventForm(request.POST, instance=Event.objects.filter(id=id).first())
            if not form.is_valid():
                return render(request, "edit_event.html", {"form": form})
            form.save()
            return redirect("/")


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
            size = req_dict["size"]
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
            user = registration.create_user_initialize(name, email, role, team, program, size)
        except registration.UserAlreadyExistsError:
            return HttpResponseBadRequest("User already exists.")

        return JsonResponse({"user_id": user.id, "username": user.username})  # type: ignore

    return HttpResponseBadRequest()


# region Link Discord


@permission_required("common_models.manage_scav", login_url='/accounts/login')
def scavenger_scoreboard(request: HttpRequest) -> HttpResponse:
    status = list(TeamPuzzleActivity.objects.filter(puzzle_completed_at=None).order_by('-puzzle__order'))
    return render(request, "scavenger_scoreboard.html", {"status": status})


@permission_required("common_models.manage_scav", login_url='/accounts/login')
def scavenger_monitor(request: HttpRequest) -> HttpResponse:
    return render(request, "scavenger_monitor.html")


@user_passes_test(lambda u: u.is_superuser)
def unregistered(request: HttpRequest) -> HttpResponse:
    users = User.objects.all().order_by("username")
    data = "Group Email [Required],Member Email,Member Type,Member Role"
    for usr in users:
        if not usr.is_superuser and not DiscordUser.objects.filter(user=usr).exists():
            data += '\n' + "unregisteredfacils@engfrosh.com," + usr.email + ",,"
    response = HttpResponse(data, 'text/csv')
    response['Content-Disposition'] = 'attachment; filename="unregistered.csv"'
    return response


@permission_required("common_models.view_links", login_url='/accounts/login')
def get_discord_link(request: HttpRequest) -> HttpResponse:
    """View to get discord linking links for users or send link emails to users."""

    if request.method == "GET":
        if not request.user.is_staff:
            team = Team.from_user(request.user)
            all_users = User.objects.all().order_by("username")
            users = []
            for user in all_users:
                if team.group in user.groups.all():
                    users += [user]
        else:
            users = User.objects.all().order_by("username")
        # Handle Webpage requests
        # TODO add check that user doesn't yet have a discord account linked.

        context = {"users": []}
        count = 0

        for usr in users:
            try:
                email_sent = UserDetails.objects.get(user=usr).invite_email_sent
            except ObjectDoesNotExist:
                email_sent = False

            if not usr.is_superuser and not DiscordUser.objects.filter(user=usr).exists():
                count += 1
                context["users"].append({
                    "username": usr.username,
                    "id": usr.id,
                    "email_sent": bool(email_sent),
                    "email": usr.email
                })
        context["count"] = count
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
        if not request.user.is_staff:
            team = Team.from_user(request.user)
            all_users = User.objects.all().order_by("username")
            users = []
            for u in all_users:
                if team.group in user.groups.all():
                    users += [u]
        else:
            users = User.objects.all().order_by("username")
        if user not in users:
            return HttpResponseBadRequest("Invalid user")
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
                    return JsonResponse({"user_id": user.id, "link": link})  # TODO fix to include https

                return JsonResponse(
                    {"user_id": user.id, "link": mlink.full_link(
                        hostname=request.get_host(),
                        login_path="/accounts/login", redirect="/accounts/link/discord")})  # TODO fix to include https

            case "send_link_email":
                if not request.user.is_superuser:
                    return HttpResponseBadRequest("You can't send emails.")
                if '@cmail.carleton.ca' in user.email:
                    return JsonResponse({"user_id": user.id})
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
                command = escape(req_dict['command'])
                return HttpResponseBadRequest(f"Invalid command: {command}")

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

# endregion


@permission_required("discord_bot_manager_discordchannel.change_discordchannel")
def manage_discord_channels(request: HttpRequest) -> HttpResponse:
    """Page for managing discord channels, such as locking and unlocking."""

    # TODO: Rewrite all of this to make it better
    if request.method == "GET":

        context = {}

        channels = DiscordChannel.objects.all()
        context["channels"] = channels

        return render(request, "discord_channels.html", context)

    else:

        return HttpResponseBadRequest("Bad http request method.")


def manage_discord_channel_groups(request: HttpRequest) -> HttpResponse:
    """Page for managing discord channel groups by tags or categories."""

    if not request.user.has_perm("discord_bot_manager.change_discordchannel"):
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_all_permissions"):
                permissions.update(backend.get_all_permissions(request.user))
        logger.debug(f"User permissions: {permissions}")
        return HttpResponseForbidden("Permission Denied")

    if request.method == "GET":

        context = {}

        tags = ChannelTag.objects.all()
        context["tags"] = tags

        # channels = DiscordChannel.objects.all()
        # context["channels"] = channels

        return render(request, "discord_channel_groups.html", context)

    elif request.method == "POST":

        if request.content_type != "application/json":
            return HttpResponseBadRequest("Invalid / missing content type.")

        req_dict = json.loads(request.body)
        if "command" not in req_dict:
            return HttpResponseBadRequest("Bad request body, missing command.")

        if req_dict["command"] == "lock_channel_group":
            try:
                channel_group = ChannelTag.objects.get(id=req_dict["tag_id"])
                channel_group.lock()
            except (ObjectDoesNotExist, KeyError):
                return HttpResponseBadRequest("Invalid tag id.")

            return HttpResponse(status=204)

        elif req_dict["command"] == "unlock_channel_group":
            try:
                channel_group = ChannelTag.objects.get(id=req_dict["tag_id"])
                channel_group.unlock()
            except (ObjectDoesNotExist, KeyError):
                return HttpResponseBadRequest("Invalid tag id.")

            return HttpResponse(status=204)

        else:
            return HttpResponseBadRequest("Invalid command.")

    else:

        return HttpResponseBadRequest("Bad http request method.")


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
                    query = DiscordRole.objects.filter(group_id=g)
                    for role in query:
                        if role.secondary_group is None or role.secondary_group in groups:
                            discord_role_ids.append(role.role_id)
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


@user_passes_test(lambda u: u.is_superuser)
def initialize_database(request: HttpRequest) -> HttpResponse:
    common_models.models.initialize_database()
    return redirect("manage_index")


@user_passes_test(lambda u: u.is_superuser)
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
                common_models.models.Team.objects.get(group=team.group)
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

        if request.content_type != "application/json":
            return HttpResponseBadRequest("Invalid / missing content type.")

        req_dict = json.loads(request.body)
        if "command" not in req_dict:
            return HttpResponseBadRequest("Bad request body, missing command.")
        if req_dict['command'] == 'toggle':
            if "puzzle" not in req_dict:
                return HttpResponseBadRequest("Bad request body, missing puzzle.")
            puzzle_id = req_dict['puzzle']
            puzzle = Puzzle.objects.filter(id=puzzle_id).first()
            if puzzle.enabled:
                puzzle.enabled = False
                puzzle.save()
                next_puzzle = puzzle.stream.get_next_enabled_puzzle(puzzle)
                for activity in TeamPuzzleActivity.objects.filter(puzzle=puzzle).all():
                    if not activity.puzzle_completed_at:
                        if next_puzzle is None:
                            activity.delete()
                        else:
                            activity.puzzle = next_puzzle
                            activity.save()
            else:
                puzzle.enabled = True
                puzzle.save()
            return HttpResponse("Successfully toggled puzzle")
        else:
            return HttpResponseBadRequest("Invalid command.")

    else:
        return HttpResponseNotAllowed(("GET", "POST"))


@permission_required("common_models.manage_scav")
def edit_scavenger_puzzle(request: HttpRequest, id: int) -> HttpResponse:
    """Page for editing scavenger puzzles"""
    puzzle = Puzzle.objects.filter(id=id).first()
    if puzzle is None:
        return HttpResponseBadRequest("Invalid puzzle id!")
    if request.method == "GET":
        context = {
            "puzzle": puzzle,
            "form": forms.PuzzleForm(instance=puzzle)
        }
        return render(request, "edit_scavenger_puzzle.html", context)
    elif request.method == "POST":
        form = forms.PuzzleForm(request.POST, instance=puzzle)
        if not form.is_valid():
            context = {
                "error": True,
                "puzzle": puzzle,
                "form": form
            }
            return render(request, "edit_scavenger_puzzle.html", context)
        form.save()
        teams = Team.objects.all()
        for team in teams:
            team.refresh_scavenger_progress()
        return redirect("manage_scavenger_puzzles")
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


@permission_required("common_models.view_discord_nicks", login_url='/accounts/login')
def manage_discord_nicks(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        search = request.GET.get('filter', '')
        if request.user.is_staff:
            users = DiscordUser.objects.filter(user__username__icontains=search)
            users |= DiscordUser.objects.filter(discord_username__icontains=search)
        else:
            team = Team.from_user(request.user)
            group = team.group
            users = DiscordUser.objects.filter(user__username__icontains=search, user__groups__id__in=[group.id])
            users |= DiscordUser.objects.filter(discord_username__icontains=search, user__groups__id__in=[group.id])
        return render(request, "manage_discord_nicks.html", {"users": users})
    elif request.method == "POST":
        if request.content_type != "application/json":
            return HttpResponseBadRequest("Not application/json content type")
        req_dict = json.loads(request.body)
        if "command" not in req_dict:
            return HttpResponseBadRequest("No command in request")
        if req_dict['command'] == 'delete':
            if request.user.is_staff:
                users = DiscordUser.objects.all()
            else:
                team = Team.from_user(request.user)
                group = team.group
                users = DiscordUser.objects.filter(user__groups__id__in=[group.id]).all()
            if "user" not in req_dict:
                return HttpResponseBadRequest("No user in request.")
            user = DiscordUser.objects.filter(id=req_dict['user']).first()
            if user not in users:
                return HttpResponseBadRequest("Invalid user.")
            user.delete()
            return HttpResponse("Unlinked discord account.")
        else:
            return HttpResponseBadRequest("Invalid command.")


@permission_required("common_models.manage_discord_nicks", login_url='/accounts/login')
def manage_discord_nick(request: HttpRequest, id: int) -> HttpResponse:
    if request.method == "GET":
        user = DiscordUser.objects.filter(id=id).first()
        form = forms.DiscordNickForm(nick=user.discord_username)
        return render(request, "manage_discord_nick.html", {"user": user, "form": form})
    elif request.method == "POST":
        user = DiscordUser.objects.filter(id=id).first()
        form = forms.DiscordNickForm(request.POST)
        context = {"user": user, "form": form, "error": False}
        if form.is_valid():
            nick = form.cleaned_data['nickname']
            color = form.cleaned_data['color'][1:]
            guild = DiscordGuild.objects.all().first()
            name = "color-"+str(color)
            role = guild.get_role(name)
            if role is None:
                role = guild.create_role(name=name, position=settings.COLOR_POSITION, color=int(color, 16))
            guild.add_role_to_member(user.id, role)
            guild.change_nick(user.id, nick)
        else:
            context['error'] = True
        return render(request, "manage_discord_nick.html", context)
