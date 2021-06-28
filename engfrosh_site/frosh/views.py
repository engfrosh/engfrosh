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
