from django.http import HttpRequest, HttpResponse
from django.shortcuts import render  # noqa F401

from common_models.models import Puzzle, Team
from django.contrib.auth.decorators import login_required, permission_required

import logging

logger = logging.getLogger("engfrosh_site.scavenger.views")


@login_required(login_url='/accounts/login')
def index(request: HttpRequest) -> HttpResponse:

    team = Team.from_user(request.user)
    if not team:
        return render(request, "scavenger_index.html", context={"team": None})

    puzzles = team.active_puzzles
    logger.debug(f"{[p.name for p in puzzles]}")

    context = {
        "team": team,
        # "puzzles": team.active_puzzles
        "puzzles": puzzles
    }

    return render(request, "scavenger_index.html", context=context)


def puzzle_view(request: HttpRequest) -> HttpResponse:
    obj = Puzzle.objects.first()
    context = {"puzzle": obj}
    return render(request, "scavenger_question.html", context)
