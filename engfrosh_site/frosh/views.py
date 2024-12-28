from django.http.response import HttpResponse, HttpResponseNotAllowed, HttpResponseForbidden
from django.shortcuts import render  # noqa F401
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required, permission_required
import random
from common_models.models import Team, TeamTradeUpActivity, VerificationPhoto, Announcement, UserDetails
from common_models.models import InclusivityPage, FroshRole, DiscordUser, Setting, FAQPage, BooleanSetting
import datetime
from management import forms
from common_models.models import Event, CalendarRelation, Calendar
from django.contrib.contenttypes.models import ContentType
import logging
from .forms import CharterForm
from django.http import HttpResponseRedirect

logger = logging.getLogger("frosh.views")


def faq_page(request: HttpRequest, id: int):
    if id == 0:
        groups = list(request.user.groups.all())
        groups += [None]
        pages = FAQPage.objects.filter(restricted__in=groups)
        pages |= FAQPage.objects.filter(restricted=None)
        return render(request, "faq_pages.html", {"pages": pages})
    else:
        groups = list(request.user.groups.all())
        groups += [None]
        page = FAQPage.objects.filter(id=id, restricted__in=groups).first()
        if page is None:
            page = FAQPage.objects.filter(id=id, restricted=None).first()
        if page is None:
            return HttpResponse("FAQ not found!", status=404)
        return render(request, "faq_page.html", {"page": page})


def fish(request: HttpRequest):
    return render(request, "fish.html", {})


def inclusivity_public(request: HttpRequest):
    return render(request, "inclusivity_public.html", {})


@login_required(login_url='/accounts/login')
def view_event(request: HttpRequest, id: int):
    e = Event.objects.filter(id=id).first()
    if e is None:
        form = None
    else:
        form = forms.EventForm(calendar_choices=[{"name": e.calendar.name}], readonly=True)
        form.initial['start'] = e.start
        form.initial['end'] = e.end
        form.initial['title'] = e.title
        form.initial['description'] = e.description
        form.initial['calendar'] = e.calendar
        form.initial['color'] = e.color_event
    context = {"form": form}
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
        d["id"] = team.group.id

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
def upload_charter(request: HttpRequest) -> HttpResponse:
    loc = Setting.objects.get_or_create(id="Blank Charter URL", defaults={"value": "http://localhost/charter.pdf"})[0]
    if request.method == "POST":
        form = CharterForm(request.POST, request.FILES)
        if not form.is_valid() or not request.FILES['file'].name.lower().endswith(".pdf"):
            return render(request, "upload_charter.html",
                          {"form": form, "charter_loc": loc.value, "error": "Invalid file!"})
        details = UserDetails.objects.get(user=request.user)
        details.charter = request.FILES['file']
        details.save()
        return HttpResponseRedirect("/user/")
    else:
        form = CharterForm()
    return render(request, "upload_charter.html", {"form": form, "charter_loc": loc.value})


@login_required(login_url='/accounts/login')
def user_home(request: HttpRequest) -> HttpResponse:
    """The home page for regular users."""

    rand = random.randint(0, 3)
    roll = Setting.objects.get_or_create(id="Rick Roll", defaults={"value": "Darwin_J-gwktdVor"})[0]
    if request.user.username != roll.value:
        rand = 0
    team = Team.from_user(request.user)
    details = UserDetails.objects.filter(user=request.user).first()

    calendars = set()
    user = request.user
    headplanning = False
    for group in user.groups.all():
        try:
            if group.name == "Head" or group.name == "Planning":
                headplanning = True
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
    if request.user.has_perm("common_models.calendar_manage"):
        calendars.update(Calendar.objects.all())

    discord = DiscordUser.objects.filter(user=request.user).first()
    upload_charter = False
    charter = Setting.objects.get_or_create(id="Charter Upload", defaults={"value": "False"})[0]
    if details is not None and charter.value == "True" and details.role != "Frosh":
        try:
            details.charter.path
        except:  # noqa: E722
            upload_charter = True
    link_discord = True if discord is None and details is not None and details.discord_allowed else False
    discord_enabled = BooleanSetting.objects.get_or_create(id="DISCORD_ENABLED")[0].value
    link_discord &= discord_enabled
    context = {
        "scavenger_enabled": team.scavenger_enabled if team else False,
        "trade_up_enabled": team.trade_up_enabled if team else False,
        "scavenger_disabled": not team.scavenger_enabled if team else False,
        "trade_up_disabled": not team.trade_up_enabled if team else False,
        "details": details,
        "link_discord": link_discord,
        "rand": rand,
        "calendars": calendars,
        "upload_charter": upload_charter,
        "headplanning": headplanning,
        "team": team
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
