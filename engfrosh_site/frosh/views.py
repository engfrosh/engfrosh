from django.http.response import HttpResponse, HttpResponseNotAllowed, HttpResponseForbidden
from django.shortcuts import render  # noqa F401
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required, permission_required
import random
from common_models.models import Team, TeamTradeUpActivity, VerificationPhoto, Announcement, UserDetails
from common_models.models import InclusivityPage, FroshRole, DiscordUser
import datetime
from management import forms
from schedule.models import Event, CalendarRelation
from django.contrib.contenttypes.models import ContentType
import logging

logger = logging.getLogger("frosh.views")


def fish(request: HttpRequest):
    return render(request, "fish.html", {})


def inclusivity_public(request: HttpRequest):
    return render(request, "inclusivity_public.html", {})


@login_required(login_url='/accounts/login')
def view_event(request: HttpRequest, id: int):
    context = {"form": forms.EventForm(instance=Event.objects.filter(id=id).first())}
    return render(request, "view_event.html", context)


@login_required(login_url='/accounts/login')
def inclusivity_private(request: HttpRequest):
    groups = request.user.groups
    frosh_groups = FroshRole.objects.all()
    names = []
    for g in frosh_groups:
        names += [g.name]
    role = groups.filter(name__in=names).first()
    access = -1
    if role is None:
        access = 0
    elif role.name == "Planning":
        access = 4
    elif role.name == "Head":
        access = 3
    elif role.name == "Facil":
        access = 2
    elif role.name == "Frosh":
        access = 1
    pages = InclusivityPage.objects.filter(permissions__lte=access, open_time__lte=datetime.datetime.now())
    pages = list(pages)
    return render(request, "inclusivity_private.html", {"pages": pages})


@permission_required('common_models.view_team_coin_standings', "/accounts/permission-denied/")
def coin_standings(request: HttpRequest):
    context = {
        "teams": []
    }

    teams = Team.objects.all().order_by("coin_amount").reverse()

    cur_place = 0
    cur_coin = None
    next_place = 1

    for team in teams:
        d = {}

        d["name"] = team.display_name
        d["coin"] = team.coin_amount

        if d["coin"] == cur_coin:
            # If there is a tie
            d["place"] = cur_place
            next_place += 1
        else:
            d["place"] = next_place
            cur_place = next_place
            next_place += 1
            cur_coin = d["coin"]

        context["teams"].append(d)

    return render(request, "scoin_standings.html", context)


@login_required(login_url='/accounts/login')
def my_coin(request: HttpRequest):
    """Get the coin standings for your team."""

    teams = Team.objects.filter(group__in=request.user.groups.all())

    if len(teams) > 0:
        context = {"team": teams[0]}
        return render(request, "team_scoin.html", context)

    return HttpResponse("You are not a part of any teams.")


def overall_index(request: HttpRequest):
    """The home page at the root of the site."""
    announcements = Announcement.objects.order_by("-created")
    return render(request, "overall_index.html", {'announcements': announcements})


@login_required(login_url='/accounts/login')
def user_home(request: HttpRequest) -> HttpResponse:
    """The home page for regular users."""

    rand = random.randint(0, 3)
    if request.user.username != "Darwin_J-gwktdVor":
        rand = 0
    team = Team.from_user(request.user)
    details = UserDetails.objects.filter(user=request.user).first()

    calendars = set()
    user = request.user
    for group in user.groups.all():
        try:
            ct = ContentType.objects.get_for_model(group)
            relations = CalendarRelation.objects.filter(content_type=ct, object_id=group.id)
            for relation in relations:
                calendars.update({relation.calendar})
        except Exception as e:
            logger.error(e)
            continue
    try:
        ct = ContentType.objects.get_for_model(user)
        relations = CalendarRelation.objects.filter(content_type=ct, object_id=user.id)
        for relation in relations:
            calendars.update({relation.calendar})
    except Exception:
        pass

    discord = DiscordUser.objects.filter(user=request.user).first()

    context = {
        "scavenger_enabled": team.scavenger_enabled if team else False,
        "trade_up_enabled": team.trade_up_enabled if team else False,
        "scavenger_disabled": not team.scavenger_enabled if team else False,
        "trade_up_disabled": not team.trade_up_enabled if team else False,
        "details": details,
        "link_discord": True if discord is None else False,
        "rand": rand,
        "calendars": calendars,
    }

    return render(request, "user_home.html", context)


def trade_up(request: HttpRequest) -> HttpResponse:
    """Upload page for trade up."""

    team = Team.from_user(request.user)
    if not team:
        return HttpResponse("Sorry you aren't on a team. If this is incorrect, please contact supoort")

    if not team.trade_up_enabled:
        return HttpResponseForbidden("Trade up is not enabled")

    match request.method:
        case "GET":

            context = {}

            return render(request, "trade_up_upload.html", context)

        case "POST":

            photo = VerificationPhoto()
            photo.photo = request.FILES["photo_upload"]
            photo.save()

            object_name = request.POST.get("object_name")

            tta = TeamTradeUpActivity(team=team, verification_photo=photo, object_name=object_name)
            tta.save()

            return HttpResponse("Success")

        case _:

            return HttpResponseNotAllowed(["GET", "POST"])
