from django.http.response import HttpResponse
from django.shortcuts import render  # noqa F401
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required, permission_required

from common_models.models import Team

# Create your views here.


@permission_required('frosh.view_team_coin_standings', "/accounts/permission-denied/")
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
    return render(request, "overall_index.html")


def user_home(request: HttpRequest) -> HttpResponse:
    """The home page for regular users."""

    team = Team.from_user(request.user)

    context = {
        "scavenger_enabled": team.scavenger_enabled if team else False
    }

    return render(request, "user_home.html", context)
