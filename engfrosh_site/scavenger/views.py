from django.http import HttpRequest, HttpResponse
from django.shortcuts import render  # noqa F401


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "scavenger.html")
