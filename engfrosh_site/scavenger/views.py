from typing import Optional, Union
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseNotAllowed, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render  # noqa F401

from common_models.models import Puzzle, Team
from django.contrib.auth.decorators import login_required, permission_required

import logging
import json

logger = logging.getLogger("engfrosh_site.scavenger.views")


@login_required(login_url='/accounts/login')
def index(request: HttpRequest) -> HttpResponse:

    team = Team.from_user(request.user)
    if not team:
        return render(request, "scavenger_index.html", context={"team": None})

    context = {
        "team": team,
        "active_puzzles": team.active_puzzles,
        "completed_puzzles": team.completed_puzzles
    }

    return render(request, "scavenger_index.html", context=context)


@login_required(login_url='/accounts/login')
def puzzle_view(request: HttpRequest, slug: str) -> HttpResponse:
    # TODO add support for lockouts
    # TODO add permission verification

    team = Team.from_user(request.user)
    if not team:
        return HttpResponse("Sorry you aren't on a team. If this is incorrect, please contact supoort")

    try:
        puz: Union[Puzzle, None] = Puzzle.objects.get(secret_id=slug)
    except Puzzle.DoesNotExist:
        puz = None

    if not (puz and puz.is_viewable_for_team(team)):
        return HttpResponse("You do not have access to this puzzle.")

    if request.method == "GET":

        context = {
            "puzzle": puz,
            "view_only": puz.is_completed_for_team(team)
        }

        return render(request, "scavenger_question.html", context)

    elif request.method == "POST":

        if request.content_type != "application/json":
            return HttpResponseBadRequest("Not application/json content type")

        req_dict = json.loads(request.body)

        if "answer" not in req_dict:
            return HttpResponseBadRequest("No answer provided in json body")

        correct, stream_completed, next_puzzle = puz.check_team_guess(team, req_dict["answer"])

        if next_puzzle:
            next_puzzle_id = next_puzzle.secret_id
        else:
            next_puzzle_id = ""

        return JsonResponse({"correct": correct, "scavenger_stream_completed": stream_completed,
                             "next_puzzle_id": next_puzzle_id, "require_verification_photo": False})
        # TODO add verification photo submission

    else:
        return HttpResponseNotAllowed(["GET", "POST"])
