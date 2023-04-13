from django.shortcuts import render  # noqa F401
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required


@login_required(login_url='/accounts/login')
def index(request: HttpRequest):
    return render(request, "calendar_index.html", {})
