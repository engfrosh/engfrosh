from django.shortcuts import render  # noqa F401
from django.http import HttpRequest

from .models import Team

# Create your views here.


def coin_standings(request: HttpRequest):
    context = {
        "teams": []
    }

    teams = Team.objects.all()

    for team in teams:
        d = {}

        d["name"] = team.display_name
        d["coin"] = team.coin_amount
        d["place"] = 0
        context["teams"].append(d)

    return render(request, "scoin_standings.html", context)
