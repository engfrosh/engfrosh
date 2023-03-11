from django.shortcuts import render  # noqa F401
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from schedule.models import Calendar, Event
from schedule.periods import weekday_names


@login_required(login_url='/accounts/login')
def index(request: HttpRequest):
    return render(request, "calendar_index.html", {})
