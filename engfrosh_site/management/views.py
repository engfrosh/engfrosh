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
from common_models.models import FroshRole, Team, UniversityProgram, TeamTradeUpActivity, UserDetails
from common_models.models import ChannelTag, DiscordGuild, Announcement, FacilShift, FacilShiftSignup
from common_models.models import Setting, QRCode
import common_models.models
from common_models.models import DiscordRole, DiscordOverwrite, BooleanSetting
from . import registration
from . import forms

from django.utils.html import escape
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http.request import HttpRequest
from django.http.response import HttpResponse, JsonResponse, \
    HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseServerError, HttpResponseForbidden
from django.shortcuts import render, redirect
from .forms import AnnouncementForm
from django.contrib.auth.decorators import user_passes_test
from schedule.models import Event, Calendar


logger = logging.getLogger("management.views")

CURRENT_DIRECTORY = os.path.dirname(__file__)
PARENT_DIRECTORY = os.path.dirname(CURRENT_DIRECTORY)


@permission_required("common_models.calendar_manage")
def show_calendars(request: HttpRequest) -> HttpResponse:
    calendars = Calendar.objects.exclude(name__in=User.objects.all().values('username'))
    return render(request, "show_calendars.html", {"calendars": calendars})


@permission_required("common_models.calendar_manage")
def edit_calendar(request: HttpRequest, id: int) -> HttpResponse:
    if id == 0:
        form = forms.CalendarForm()
    else:
        cal = Calendar.objects.filter(id=id).first()
        form = forms.CalendarForm(instance=cal)
    return render(request, "edit_calendar.html", {"form": form})


@permission_required("common_models.lock_scav")
def lock_scav(request: HttpRequest) -> HttpResponse:
    scav = BooleanSetting.objects.get(id="SCAVENGER_ENABLED")
    tradeup = BooleanSetting.objects.get(id="TRADE_UP_ENABLED")
    if request.method == "POST":
        scav.value = not scav.value
        tradeup.value = not tradeup.value
        scav.save()
        tradeup.save()
        scav_txt = "locked"
        if scav.value:
            scav_txt = "unlocked"
        tradeup_txt = "locked"
        if tradeup.value:
            tradeup_txt = "unlocked"
        DiscordChannel.send_to_updates_channels("Scav is now " + scav_txt + ". Trade Up is now " + tradeup_txt)
    return render(request, "lock_scav.html", {"scav": scav.value, "tradeup": tradeup.value})


@permission_required("common_models.shift_manage")
def shift_edit(request: HttpRequest, id: int) -> HttpResponse:
    if id == 0:
        form = forms.ShiftForm()
    else:
        shift = FacilShift.objects.filter(id=id).first()
        form = forms.ShiftForm(instance=shift)
    return render(request, "edit_shift.html", {"form": form})


@permission_required("common_models.facil_signup")
def facil_shifts(request: HttpRequest) -> HttpResponse:
    lockout_time = int(Setting.objects.get_or_create(id="Facil Shift Drop Deadline",
                                                     defaults={"value": "0"})[0].value)
    can_remove = True
    if datetime.datetime.utcfromtimestamp(lockout_time) <= datetime.datetime.now() and lockout_time != 0:
        can_remove = False
    if request.method == "GET":
        shifts = list(FacilShift.objects.all())
        rshifts = []
        for shift in shifts:
            signups = shift.facil_count
            u_signups = len(FacilShiftSignup.objects.filter(shift=shift, user=request.user))
            if signups < shift.max_facils and u_signups == 0 and not shift.is_passed:
                rshifts += [shift]
        my_shifts = []
        for shift in FacilShiftSignup.objects.filter(user=request.user):
            my_shifts += [shift.shift]
        return render(request, "facil_shift_signup.html",
                      {"shifts": rshifts, "my_shifts": my_shifts, "can_remove": can_remove})
    elif request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add":
            logger.info(request.user)
            logger.info("Signing up for facil shift. Shift id: ")
            shift_id = int(request.POST["shift_id"])
            logger.info(shift_id)
            shift = FacilShift.objects.filter(id=shift_id).first()
            shifts = list(FacilShift.objects.all())
            shifts = list(FacilShift.objects.all())
            rshifts = []
            my_shifts = []
            for shift2 in FacilShiftSignup.objects.filter(user=request.user):
                my_shifts += [shift2.shift]
            for s in shifts:
                signups = s.facil_count
                u_signups = len(FacilShiftSignup.objects.filter(shift=shift, user=request.user))
                if signups < s.max_facils and u_signups == 0 and not shift.is_passed:
                    rshifts += [s]
            if shift is None:
                logger.info("Shift not found")
                return render(request, "facil_shift_signup.html",
                              {"shifts": rshifts, "success": False, "my_shifts": my_shifts, "can_remove": can_remove})
            if shift.is_passed:
                logger.info("Shift is passed")
                return render(request, "facil_shift_signup.html",
                              {"shifts": rshifts, "success": False, "my_shifts": my_shifts, "can_remove": can_remove})
            count = len(FacilShiftSignup.objects.filter(shift=shift))
            if count >= shift.max_facils:
                logger.info("Full shift")
                return render(request, "facil_shift_signup.html",
                              {"shifts": rshifts, "success": False, "my_shifts": my_shifts, "can_remove": can_remove})
            signup = FacilShiftSignup.objects.filter(user=request.user, shift=shift).first()
            if signup is not None:
                logger.info("Already signed up")
                return render(request, "facil_shift_signup.html",
                              {"shifts": rshifts, "success": False, "my_shifts": my_shifts, "can_remove": can_remove})
            signup = FacilShiftSignup(user=request.user, shift=shift)
            signup.save()
            calendar = Calendar.objects.filter(name=request.user.username).first()
            if calendar is None:
                calendar = Calendar(name=request.user.username, slug=request.user.username)
                calendar.save()
                calendar.create_relation(request.user)
            event = Event(start=shift.start, end=shift.end, title=shift.name, description=shift.desc, calendar=calendar)
            event.save()
            shifts = list(FacilShift.objects.all())
            rshifts = []
            for shift in shifts:
                signups = shift.facil_count
                count = len(FacilShiftSignup.objects.filter(shift=shift, user=request.user))
                if signups < shift.max_facils and count == 0 and not shift.is_passed:
                    rshifts += [shift]
            logger.info("Signed up for shift")
            my_shifts = []
            for shift in FacilShiftSignup.objects.filter(user=request.user):
                my_shifts += [shift.shift]
            return render(request, "facil_shift_signup.html",
                          {"shifts": rshifts, "success": True, "my_shifts": my_shifts, "can_remove": can_remove})
        elif action == "remove":
            my_shifts = []
            for shift in FacilShiftSignup.objects.filter(user=request.user):
                my_shifts += [shift.shift]
            logger.info(request.user)
            logger.info("Removing from facil shift. Shift id: ")
            if not can_remove:
                logger.info("Removing is disabled")
                return render(request, "facil_shift_signup.html",
                              {"shifts": rshifts, "success": False, "my_shifts": my_shifts, "can_remove": can_remove})
            shift_id = int(request.POST["shift_id"])
            logger.info(shift_id)
            shift = FacilShift.objects.filter(id=shift_id).first()
            if shift is None:
                logger.info("Shift not found")
                return render(request, "facil_shift_signup.html",
                              {"shifts": rshifts, "success": False, "my_shifts": my_shifts, "can_remove": can_remove})
            if shift.is_cutoff:
                logger.info("Shift is cutoff")
                return render(request, "facil_shift_signup.html",
                              {"shifts": rshifts, "success": False, "my_shifts": my_shifts, "can_remove": can_remove})
            signup = FacilShiftSignup.objects.filter(shift=shift, user=request.user).first()
            if signup is None:
                logger.info("Shift not found")
                rshifts = []
                shifts = list(FacilShift.objects.all())
                for shift in shifts:
                    signups = shift.facil_count
                    count = len(FacilShiftSignup.objects.filter(shift=shift, user=request.user))
                    if signups < shift.max_facils and count == 0 and not shift.is_passed:
                        rshifts += [shift]
                return render(request, "facil_shift_signup.html",
                              {"shifts": rshifts, "success": False, "my_shifts": my_shifts, "can_remove": can_remove})
            signup.delete()
            user = request.user
            calendar = Calendar.objects.filter(name=user.username).first()
            if calendar is not None:
                calendar.delete()
            calendar = Calendar(name=user.username, slug=user.username)
            calendar.save()
            calendar.create_relation(user)

            signups = list(FacilShiftSignup.objects.filter(user=user))
            for signup in signups:
                shift = signup.shift
                event = Event(start=shift.start, end=shift.end, title=shift.name,
                              description=shift.desc, calendar=calendar)
                event.save()
            my_shifts = []
            for shift in FacilShiftSignup.objects.filter(user=request.user):
                my_shifts += [shift.shift]
            rshifts = []
            shifts = list(FacilShift.objects.all())
            for shift in shifts:
                signups = shift.facil_count
                count = len(FacilShiftSignup.objects.filter(shift=shift, user=request.user))
                if signups < shift.max_facils and count == 0 and not shift.is_passed:
                    rshifts += [shift]
            return render(request, "facil_shift_signup.html",
                          {"shifts": rshifts, "success": True, "my_shifts": my_shifts, "can_remove": can_remove})


@permission_required("common_models.shift_manage")
def mailing_list(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        shifts = list(FacilShift.objects.order_by('start'))
        return render(request, "create_mailing_list.html", {"shifts": shifts})
    elif request.method == "POST":
        shift_id = int(request.POST["shift_id"])
        shift = FacilShift.objects.filter(id=shift_id).first()
        signups = list(FacilShiftSignup.objects.filter(shift=shift))
        redir = ""
        for signup in signups:
            redir += "," + signup.user.email
        redir = "mailto:" + redir[1:]
        return HttpResponse('<meta http-equiv="refresh" content="0;url=' + redir + '" />')


@permission_required("common_models.report_manage")
def reports(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        details = UserDetails.objects.all().first()
        params = []
        for key in dir(details):
            if key.startswith("_"):
                continue
            params += ["details." + key]
        for key in dir(details.user):
            if key.startswith("_"):
                continue
            params += ["user." + key]
        return render(request, "reports.html", {"params": params})
    elif request.method == "POST":
        req_dict = json.loads(request.POST.get("query"))
        requirements = []
        try:
            dataformat = req_dict['format']
            for query in req_dict['query']:
                target = query['target']
                value = query['value']
                operator = query['operator']
                requirements += [(target, value, operator)]
        except KeyError:
            return HttpResponseBadRequest("Key Error in Body")
        users = UserDetails.objects.all()
        data = []
        for user in users:
            met = True
            for r in requirements:
                d = r[0].split(".")
                obj = d[0]
                name = d[1]
                if obj == "details":
                    value = str(getattr(user, name))
                    if callable(value):
                        value = value()
                elif obj == "user":
                    value = str(getattr(user.user, name))
                    if callable(value):
                        value = value()
                if r[2] == "=" and value.lower() != str(r[1]).lower():
                    met = False
                    break
                elif r[2] == "!=" and value.lower() == str(r[1]).lower():
                    met = False
                    break
                elif r[2] == "ew" and not value.lower().endswith(str(r[1]).lower()):
                    met = False
                    break
                elif r[2] == "new" and value.lower().endswith(str(r[1]).lower()):
                    met = False
                    break
            if met:
                data += [user]
        output = []
        first = True
        for user in data:
            cur = []
            if first:
                for key in user.__dict__.keys():
                    if key.startswith("_"):
                        continue
                    cur += ["details." + key]
                cur += ["details.role"]
                for key in user.user.__dict__.keys():
                    if key.startswith("_"):
                        continue
                    cur += ["user." + key]
                output += [cur]
            cur = []
            first = False
            for key, value in user.__dict__.items():
                if key.startswith("_"):
                    continue
                cur += [str(value)]
            cur += [user.role]
            for key, value in user.user.__dict__.items():
                if key.startswith("_"):
                    continue
                cur += [str(value)]
            output += [cur]
        if dataformat == "csv":
            line = ""
            for o1 in output:
                for o2 in o1:
                    line += o2 + ","
                line += "\n"
            response = HttpResponse(line, content_type="text/csv")
            response['Content-Disposition'] = 'attachment; filename="report.csv"'
            return response
        elif dataformat == "html":
            req_dict["format"] = "csv"
            return render(request, "reports.html", {"data": output, "length": len(output)-1,
                                                    "query": json.dumps(req_dict)})


@permission_required("common_models.calendar_manage")
def shift_manage(request: HttpRequest, id: int) -> HttpResponse:
    if request.method == "GET":
        if id == 0:
            users = list(User.objects.all())
            return render(request, "shift_manage_lookup.html", {"users": users})
        else:
            shifts = list(FacilShiftSignup.objects.filter(user__pk=id))
            return render(request, "shift_manage.html", {"shifts": shifts})
    else:
        if id != 0:
            shift_id = int(request.POST["shift"])
            if shift_id != -1:
                signup = FacilShiftSignup.objects.filter(shift__pk=shift_id, user__pk=id).first()
                shift = signup.shift
                signup.delete()

            user = User.objects.filter(id=id).first()
            calendar = Calendar.objects.filter(name=user.username).first()
            if calendar is not None:
                calendar.delete()
            calendar = Calendar(name=user.username, slug=user.username)
            calendar.save()
            calendar.create_relation(user)

            signups = list(FacilShiftSignup.objects.filter(user__pk=id))
            for signup in signups:
                shift = signup.shift
                event = Event(start=shift.start, end=shift.end, title=shift.name,
                              description=shift.desc, calendar=calendar)
                event.save()

            shifts = list(FacilShiftSignup.objects.filter(user__pk=id))
            return render(request, "shift_manage.html", {"shifts": shifts})
        else:
            for user in User.objects.all():
                calendar = Calendar.objects.filter(name=user.username).first()
                if calendar is not None:
                    calendar.delete()
                calendar = Calendar(name=user.username, slug=user.username)
                calendar.save()
                calendar.create_relation(user)

                signups = list(FacilShiftSignup.objects.filter(user=user))
                for signup in signups:
                    shift = signup.shift
                    event = Event(start=shift.start, end=shift.end, title=shift.name,
                                  description=shift.desc, calendar=calendar)
                    event.save()
            users = list(User.objects.all())
            return render(request, "shift_manage_lookup.html", {"users": users})


@permission_required("common_models.shift_manage")
def shift_export(request: HttpRequest) -> HttpResponse:
    shifts = list(FacilShift.objects.all())
    signups = list()
    longest = 0
    line = ""
    signups = FacilShiftSignup.objects.all()
    shift_signups = []
    for shift in shifts:
        if shift.facil_count > longest:
            longest = shift.facil_count
        line += shift.name.replace(',', '') + ","
        s = []
        for signup in signups:
            if signup.shift == shift:
                s += [signup]
        shift_signups += [s]
    for i in range(longest):
        line += "\n"
        for j in range(len(shift_signups)):
            signup = shift_signups[j]
            if len(signup) > i:
                user = signup[i].user
                line += user.first_name + " " + user.last_name + ","
            else:
                line += ","
    response = HttpResponse(line, content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="shifts.csv"'
    return response


@permission_required("common_models.report_manage")
def export_teams(request: HttpRequest) -> HttpResponse:
    data = {}
    max_len = 0
    for team in Team.objects.all():
        users = UserDetails.objects.filter(user__groups__in=[team.group])
        data[team] = users
        if len(users) > max_len:
            max_len = len(users)
    line = ""
    for i in range(-2, max_len):
        for key, value in data.items():
            if i == -2:
                line += key.display_name + ",,"
            elif i == -1:
                line += "Name,Role,"
            else:
                if len(value) > i:
                    line += value[i].name + "," + value[i].role + ","
                else:
                    line += ",,"

        line += "\n"

    response = HttpResponse(line, content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="teams.csv"'
    return response


@permission_required("common_models.announcement_manage")
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
def free_hints(request: HttpRequest, id: int) -> HttpResponse:
    if request.method == "GET":
        if id == 0:
            return render(request, "free_hints.html", {"teams": Team.objects.all()})
        else:
            team = Team.objects.filter(group_id=id).first()
            form = forms.HintForm()
            form.free_hints = team.free_hints

            return render(request, "free_hint.html", {"team": team, "form": form})
    elif request.method == "POST":
        team = Team.objects.filter(group_id=id).first()
        form = forms.HintForm(request.POST)
        if not form.is_valid():
            return render(request, "free_hint.html", {"team": team, "form": form, "error": True})
        team.free_hints = form.cleaned_data['free_hints']
        team.save()
        return redirect("/manage/free_hints/0")


@permission_required("common_models.manage_scav")
def lock_team(request: HttpRequest, id: int) -> HttpResponse:
    for team in Team.objects.exclude(scavenger_locked_out_until=None):
        if not team.scavenger_lock:
            team.scavenger_locked_out_until = None
            team.save()
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
    for team in Team.objects.exclude(scavenger_locked_out_until=None):
        if not team.scavenger_lock:
            team.scavenger_locked_out_until = None
            team.save()
    if id == 0:
        return render(request, "unlock_teams.html", {"teams": Team.objects.all()})
    else:
        team = Team.objects.filter(group_id=id).first()
        team.scavenger_locked_out_until = None
        team.save()
        return redirect("/manage/unlock_team/0")


@permission_required("common_models.calendar_manage")
def edit_event(request: HttpRequest, id: int) -> HttpResponse:
    if request.method == "GET":
        event = Event.objects.filter(id=id).first()
        form = forms.EventForm()
        if id != 0:
            form.start = event.start
            form.end = event.end
            form.title = event.title
            form.description = event.description
            form.calendar = event.calendar.name
            form.color_event = event.color_event
        else:
            form.start = datetime.datetime.now()
            form.end = datetime.datetime.now()
            form.title = ""
            form.description = ""
            form.calendar = ""
            form.color_event = ""
        context = {"form": form}
        return render(request, "edit_event.html", context)
    elif request.method == "POST":
        action = request.POST['action']
        if action == "delete":
            event = Event.objects.filter(id=id).first()
            if event is not None:
                event.delete()
            return redirect("/")
        elif action == "modify":
            form = forms.EventForm(request.POST)
            if not form.is_valid():
                return render(request, "edit_event.html", {"form": form})
            data = form.cleaned_data
            start = data['start']
            end = data['end']
            title = data['title']
            desc = data['description']
            calendar = data['calendar']
            color = data['color_event']
            for c in calendar:
                cal = Calendar.objects.get(name=c)
                event = Event(start=start, end=end, title=title, description=desc, calendar=cal, color_event=color)
                event.save()
            return redirect("/manage/")


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
            rafting = req_dict["rafting"]
            sweater = req_dict["sweater"]
            if rafting.lower() == "true":
                rafting = True
            else:
                rafting = False
            hardhat = req_dict["hardhat"]
            if hardhat.lower() == "true":
                hardhat = True
            else:
                hardhat = False
            allergies = req_dict["allergies"]
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
            user = registration.create_user_initialize(name, email, role, team, program, size,
                                                       rafting=rafting, hardhat=hardhat,
                                                       allergies=allergies, sweater_size=sweater)
        except registration.UserAlreadyExistsError:
            return HttpResponseBadRequest("User already exists.")

        return JsonResponse({"user_id": user.id, "username": user.username})  # type: ignore

    return HttpResponseBadRequest()


@permission_required("auth.change_user")
def bulk_add_prc(request: HttpRequest) -> HttpResponse:
    """View for bulk prc adding."""

    if request.method == "GET":
        context = {}
        return render(request, "bulk_prc_add.html", context)

    elif request.method == "POST":

        if request.content_type != "application/json":
            return HttpResponseBadRequest("Not application/json content type")

        req_dict = json.loads(request.body)
        try:
            if req_dict["command"] != "add_prc":
                return HttpResponseBadRequest()

            first_name = req_dict["first_name"]
            last_name = req_dict["last_name"]
            email = req_dict["email"]
            issued = req_dict["issued"]
        except KeyError:
            return HttpResponseBadRequest("Key Error in Body")
        if issued is None or issued == "":
            return HttpResponseBadRequest("Invalid PRC.")
        user = User.objects.filter(email=email).first()
        if user is None:
            users = User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name)
            if len(users) == 1:
                user = users.first()
        if user is None:
            return HttpResponseBadRequest("User not found.")
        details = UserDetails.objects.filter(user=user).first()
        details.prc_completed = True
        details.save

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
    users = User.objects.select_related("discorduser").all().order_by("username")
    data = "Group Email [Required],Member Email,Member Type,Member Role"
    for usr in users:
        if not usr.is_superuser:
            try:
                d = usr.discorduser  # noqa: F841
            except Exception:
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
            group = team.group
            users = User.objects.select_related("discorduser").select_related("userdetails").filter(groups__in=[group]).order_by("username")  # noqa: E501
        else:
            users = User.objects.select_related("discorduser").select_related("userdetails").order_by("username")
        # Handle Webpage requests
        # TODO add check that user doesn't yet have a discord account linked.

        context = {"users": []}
        count = 0
        for usr in users:
            try:
                d = usr.userdetails
                if d is None or not d.invite_email_sent:
                    email_sent = False
                else:
                    email_sent = True
                try:
                    discord = usr.discorduser  # noqa: F841
                except Exception:
                    if not usr.is_superuser:
                        count += 1
                        context["users"].append({
                            "username": usr.username,
                            "id": usr.id,
                            "email_sent": bool(email_sent),
                            "email": usr.email
                        })
            except Exception:
                pass
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
            group = team.group
            users = User.objects.filter(groups__in=[group]).order_by("username")
        else:
            users = User.objects.all().order_by("username")
        if user not in users:
            return HttpResponseBadRequest("Invalid user")
        if DiscordUser.objects.filter(user=user).first() is not None:
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


@user_passes_test(lambda u: u.is_superuser)
def discord_rename(request: HttpRequest) -> HttpResponse:
    for channel in DiscordChannel.objects.all():
        channel.rename()
    for role in DiscordRole.objects.all():
        role.rename()
    return redirect('/manage/')


@user_passes_test(lambda u: u.is_superuser)
def discord_create(request: HttpRequest) -> HttpResponse:
    guild = DiscordGuild.objects.first()
    if guild is None:
        return redirect('/manage/')
    types = [
        ("Frosh", ChannelTag.objects.get_or_create(name="FROSH")[0], Group.objects.get_or_create(name="Frosh")[0]),
        ("Facil", ChannelTag.objects.get_or_create(name="FACIL")[0], Group.objects.get_or_create(name="Facil")[0]),
        ("Design", ChannelTag.objects.get_or_create(name="DESIGN")[0], Group.objects.get_or_create(name="Design")[0]),
        ("Head", ChannelTag.objects.get_or_create(name="HEAD")[0], Group.objects.get_or_create(name="Head")[0]),
        ("Groupco", ChannelTag.objects.get_or_create(name="GROUP-CO")[0],
         Group.objects.get_or_create(name="GroupCo")[0]),
    ]
    if guild.get_role("Planning") is None:
        r = guild.create_role("Planning")
    else:
        r = guild.get_role("Planning")
    g = Group.objects.get_or_create(name="Planning")[0]
    dr = DiscordRole.objects.get_or_create(role_id=r.id, group_id=g)[0]
    dr.save()
    prole = DiscordRole.objects.get(group_id=Group.objects.filter(name="Planning").first())
    poverwrite = DiscordOverwrite(descriptive_name="Planning", user_id=prole.role_id, type=0, allow=3072, deny=0)
    poverwrite.save()
    disallow = DiscordOverwrite(descriptive_name="Deny All", user_id=guild.id, type=0, allow=0, deny=3072)
    disallow.save()
    admin = DiscordOverwrite.objects.get(descriptive_name="Technical")
    for team in Team.objects.all():
        if team.discord_name is None:
            continue
        overwrites = []
        for t in types:
            name = team.display_name + " " + t[0]
            if t[0] == "Design":
                name = "Design"
            sg = t[2]

            if guild.get_role(name) is None and len(DiscordRole.objects
                                                    .filter(group_id=team.group, secondary_group_id=sg) == 0):
                r = guild.create_role(name)
                dr = DiscordRole(role_id=r.id, group_id=team.group, secondary_group_id=sg)
                dr.save()
            if not t[0] == "Design":
                dr = DiscordRole.objects.filter(group_id=team.group, secondary_group_id=sg).first()
            else:
                dr = DiscordRole.objects.filter(group_id=Group.objects.filter(name=t[0]).first().id).first()
            o = DiscordOverwrite(descriptive_name=team.display_name + " " + t[0],
                                 user_id=dr.role_id, type=0, allow=3072, deny=0)
            o.save()
            overwrites += [o]
        if len(DiscordChannel.objects.filter(name=team.display_name, type=4)) == 0:
            category = guild.create_channel(team.display_name, None, True)
            DiscordChannel(name=team.display_name, type=4, id=category.id, team=team).save()
        cat = DiscordChannel.objects.filter(name=team.display_name, type=4).first()
        for i in range(len(types) - 1):
            t = types[i]
            if len(DiscordChannel.objects.filter(name=team.discord_name + "-" + t[0])) > 0:
                continue
            chan = guild.create_channel(team.discord_name + "-" + t[0], cat.id, False)
            dchan = DiscordChannel(name=team.discord_name + "-" + t[0], type=0, id=chan.id, team=team)
            dchan.save()
            dchan.tags.add(t[1])
            dchan.unlocked_overwrites.add(disallow)
            dchan.unlocked_overwrites.add(admin)
            if i == 0:
                dchan.unlocked_overwrites.add(poverwrite)
            for i2 in range(i, len(types)):
                if not (i2 == 2) or i == 2:
                    dchan.unlocked_overwrites.add(overwrites[i2])

            dchan.save()
            dchan.unlock()
    return redirect('/manage/')


@user_passes_test(lambda u: u.is_superuser)
def manage_discord_channel_groups(request: HttpRequest) -> HttpResponse:
    """Page for managing discord channel groups by tags or categories."""

    if not request.user.has_perm("discord_bot_manager.change_discordchannel"):
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_all_permissions"):
                permissions.update(backend.get_all_permissions(request.user))
        logger.info(f"User permissions: {permissions}")
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
            logger.info(f"Trying to add website user with id {req_dict['user_id']}")
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


def manage_index(request: HttpRequest) -> HttpResponse:
    """Home page for management."""
    if not request.user.is_authenticated:
        return redirect('/accounts/login')
    if not request.user.is_staff:
        return redirect('/')
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
                "scav_channel": scav_channel,
                "free_hints": team.free_hints
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

            logger.info(f"Request: {req_dict}")

            if "team_color" in req_dict and isinstance(req_dict["team_color"], int):
                logger.info(f"Setting team color to : {req_dict['team_color']}")
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
            if len(QRCode.objects.filter(puzzle=puz)) == 0:
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
                puzzle.enabled = True
                puzzle.save()
                for activity in TeamPuzzleActivity.objects.filter(puzzle=puzzle).all():
                    if not activity.is_completed:
                        if next_puzzle is None:
                            activity.delete()
                        else:
                            activity.puzzle = next_puzzle
                            activity.save()
                puzzle.enabled = False
                puzzle.save()
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
            filter(TeamPuzzleActivity._is_awaiting_verification,
                   TeamPuzzleActivity.objects.exclude(puzzle_completed_at=None)))}

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
