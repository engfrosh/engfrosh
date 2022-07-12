from django.http import HttpRequest, HttpResponse
from django.shortcuts import render  # noqa F401

from common_models.models import Puzzle


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "scavenger_index.html")


def puzzle_view(request: HttpRequest) -> HttpResponse:
    obj = Puzzle.objects.first()
    context = {"puzzle": obj}
    return render(request, "scavenger_question.html", context)
