from django.http.response import HttpResponse
from django.shortcuts import render  # noqa F401
from django.http import HttpRequest
from django.contrib.auth.decorators import permission_required

from .models import Team

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


def my_coin(request: HttpRequest):
    """Get the coin standings for your team."""

    teams = Team.objects.filter(group__in=request.user.groups.all())

    if len(teams) > 0:
        return HttpResponse(f"{teams[0].display_name} has {teams[0].coin_amount} scoin.")

    return HttpResponse("You are not a part of any teams.")


def overall_index(request: HttpRequest):
    """The home page at the root of the site."""
    return render(request, "overall_index.html")
