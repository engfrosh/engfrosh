from typing import Union
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseNotAllowed, HttpResponseBadRequest, JsonResponse, HttpResponseForbidden
from django.shortcuts import render  # noqa F401

from common_models.models import DiscordChannel, Puzzle, Team, VerificationPhoto
from django.contrib.auth.decorators import login_required

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
    bypass = request.user.has_perm('common_models.bypass_scav_rules')
    if not (puz and puz.is_viewable_for_team(team)) and not bypass:
        return HttpResponse("You do not have access to this puzzle.")

    if request.method == "GET":

        context = {
            "puzzle": puz,
            "view_only": not bypass and puz.is_completed_for_team(team) or not team.scavenger_enabled,
            "scavenger_enabled_for_team": team.scavenger_enabled,
            "guess": request.GET.get("answer", ""),
            "requires_photo": puz.requires_verification_photo_by_team(team)
        }

        return render(request, "scavenger_question.html", context)

    elif request.method == "POST":

        if not request.user.has_perm("common_models.guess_scavenger_puzzle"):
            return HttpResponseBadRequest("You are not allowed to guess.")

        if request.content_type != "application/json":
            return HttpResponseBadRequest("Not application/json content type")

        req_dict = json.loads(request.body)

        if "answer" not in req_dict:
            return HttpResponseBadRequest("No answer provided in json body")

        if not team.scavenger_enabled:
            return HttpResponseForbidden("Scavenger not currently enabled.")

        logger.debug(f"Answer submitted by team {team} with answer: {req_dict['answer']} through the website")
        if not bypass:
            correct, stream_completed, next_puzzle, require_verification_photo = puz.check_team_guess(
                team, req_dict["answer"])
            if correct:
                DiscordChannel.send_to_updates_channels(
                    f"""{team.display_name} has submitted an answer to the scav site!""")

            if require_verification_photo:
                next_page = "verification_photo/"
            elif next_puzzle:
                next_page = "../" + next_puzzle.secret_id
            else:
                next_page = ""

            return JsonResponse({"correct": correct, "scavenger_stream_completed": stream_completed,
                                "next": next_page})
        else:
            if puz.answer.lower() == req_dict["answer"].lower():
                return JsonResponse({"correct": True, "scavenger_stream_completed": None,
                                    "next": "/scavenger/"})
            else:
                return JsonResponse({"correct": False, "scavenger_stream_completed": None,
                                    "next": ""})
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
            if "photo_upload" not in request.FILES:
                return HttpResponseBadRequest("No image file provided.")
            photo.photo = request.FILES["photo_upload"]
            photo.save()

            pa.verification_photo = photo
            pa.save()

            DiscordChannel.send_to_updates_channels(
                f"""{team.display_name} has uploaded a photo for {puz.name} that needs verification.""" +
                f""""\n{request.build_absolute_uri(reverse("approve_scavenger_puzzles"))}""")

            return HttpResponse()

        case _:

            return HttpResponseNotAllowed(["GET", "POST"])
