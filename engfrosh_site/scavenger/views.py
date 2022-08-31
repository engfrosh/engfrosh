from typing import Union
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseNotAllowed, HttpResponseBadRequest, JsonResponse, HttpResponseForbidden
from django.shortcuts import render  # noqa F401

from common_models.models import DiscordChannel, Puzzle, Team, VerificationPhoto
from django.contrib.auth.decorators import login_required, permission_required

import logging
import json

from django.urls import reverse

logger = logging.getLogger("engfrosh_site.scavenger.views")


@login_required(login_url='/accounts/login')
def index(request: HttpRequest) -> HttpResponse:

    team = Team.from_user(request.user)
    if not team:
        return render(request, "scavenger_index.html", context={"team": None})

    if not team.scavenger_enabled:
        return HttpResponse("Scavenger not currently enabled")

    context = {
        "scavenger_enabled_for_team": team.scavenger_enabled,
        "team": team,
        "active_puzzles": team.active_puzzles,
        "verified_puzzles": team.verified_puzzles,
        "completed_puzzles_awaiting_verification": team.completed_puzzles_awaiting_verification,
        "completed_puzzles_requiring_photo_upload": team.completed_puzzles_requiring_photo_upload
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
            "view_only": puz.is_completed_for_team(team) or not team.scavenger_enabled,
            "scavenger_enabled_for_team": team.scavenger_enabled,
            "guess": request.GET.get("answer", "")
        }

        return render(request, "scavenger_question.html", context)

    elif request.method == "POST":

        if request.content_type != "application/json":
            return HttpResponseBadRequest("Not application/json content type")

        req_dict = json.loads(request.body)

        if "answer" not in req_dict:
            return HttpResponseBadRequest("No answer provided in json body")

        if not team.scavenger_enabled:
            return HttpResponseForbidden("Scavenger not currently enabled.")

        correct, stream_completed, next_puzzle, require_verification_photo = puz.check_team_guess(
            team, req_dict["answer"])

        if require_verification_photo:
            next_page = "verification_photo/"
        elif next_puzzle:
            next_page = "../" + next_puzzle.secret_id
        else:
            next_page = ""

        return JsonResponse({"correct": correct, "scavenger_stream_completed": stream_completed,
                             "next": next_page})

    else:
        return HttpResponseNotAllowed(["GET", "POST"])


@login_required(login_url='/accounts/login')
def puzzle_photo_verification_view(request: HttpRequest, slug: str) -> HttpResponse:

    team = Team.from_user(request.user)
    if not team:
        return HttpResponse("Sorry you aren't on a team. If this is incorrect, please contact supoort")

    try:
        puz: Union[Puzzle, None] = Puzzle.objects.get(secret_id=slug)
    except Puzzle.DoesNotExist:
        puz = None

    if not (puz and puz.is_viewable_for_team(team)):
        return HttpResponse("You do not have access to this puzzle.")

    if not puz.requires_verification_photo_by_team(team):
        return HttpResponse("You do not need to verify for this puzzle.")

    match request.method:
        case "GET":

            context = {}

            return render(request, "scavenger_verification_photo_upload.html", context)

        case "POST":

            pa = puz.puzzle_activity_from_team(team)
            if not pa:
                return HttpResponseForbidden()

            photo = VerificationPhoto()
            photo.photo = request.FILES["photo_upload"]
            photo.save()

            pa.verification_photo = photo
            pa.save()

            DiscordChannel.send_to_scavenger_updates_channels(
                f"""{team.display_name} has uploaded a photo for {puz.name} that needs verification.\n{request.build_absolute_uri(reverse("approve_scavenger_puzzles"))}""")

            return HttpResponse()

        case _:

            return HttpResponseNotAllowed(["GET", "POST"])
