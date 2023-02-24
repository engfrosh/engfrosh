from django.shortcuts import render  # noqa F401
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from schedule.models import Calendar, Event
from schedule.periods import weekday_names


@login_required(login_url='/accounts/login')
def index(request: HttpRequest):
    context = {}
    context['date'] = timezone.now()
    calendars = Calendar.objects.get_calendars_for_object(request.user)
    for group in request.user.groups.all():
        calendars = calendars | Calendar.objects.get_calendars_for_object(group)
    if not calendars:
        return None

    event_list = Event.objects.filter(calendar=calendars.first())
    first = True
    for c in calendars:
        if first:
            first = False
            continue
        event_list | Event.objects.filter(calendar=c)
    # context['period'] = period_class(event_list, date, tzinfo=local_timezone)
    context['calendar'] = calendars.first()
    context['weekday_names'] = weekday_names
    # context['here'] = quote(self.request.get_full_path())
    return render(request, "schedule/calendar_week.html", {})
