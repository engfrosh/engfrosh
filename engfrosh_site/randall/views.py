from common_models.models import RandallBooking, RandallLocation, RandallBlocked, DiscordChannel
from django.http.response import HttpResponse, HttpResponseNotAllowed, HttpResponseForbidden
from django.shortcuts import render, redirect  # noqa F401
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required, permission_required
import logging
from .forms import RandallBookingForm

logger = logging.getLogger("engfrosh_site.randall.views")

def is_randall_available(start, end):
    start = start.timestamp()
    end = end.timestamp()
    bookings = RandallBooking.objects.filter(approved=True)
    blocked = RandallBlocked.objects.all()
    for block in blocked:
        if blocked.start.timestamp() >= start and blocked.start <= end:
            return False
        if blocked.end.timestamp() >= start and blocked.end.timestamp() <= end:
            return False
    for booking in bookings:
        print(booking.start.timestamp(), booking.end.timestamp(), start, end)
        if booking.start.timestamp() >= start and booking.start.timestamp() <= end:
            return False
        if booking.end.timestamp() >= start and booking.end.timestamp() <= end:
            return False
    return True

@permission_required("common_models.manage_randall", login_url='/accounts/login')
def manage(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        id = request.POST.get("id", 0)
        action = request.POST.get("action", "")
        if id != 0 and action != "":
            booking = RandallBooking.objects.get(id=id)
            if action == "approve":
                if not is_randall_available(booking.start, booking.end):
                    pending = RandallBooking.objects.filter(approved=False).select_related("user__details")
                    approved = RandallBooking.objects.filter(approved=True).select_related("user__details").order_by("-start")
                    
                    return render(request, "randall_manage.html", context={"pending": pending, "approved": approved, "error": "booking conflict"})
                else:
                    booking.approved = True
                    booking.save()
            elif action == "delete":
                booking.delete()
            elif action == "unapprove":
                booking.approved = False
                booking.save()
    pending = RandallBooking.objects.filter(approved=False).select_related("user__details")
    approved = RandallBooking.objects.filter(approved=True).select_related("user__details").order_by("-start")
    
    return render(request, "randall_manage.html", context={"pending": pending, "approved": approved})

@permission_required("common_models.view_randall", login_url='/accounts/login')
def index(request: HttpRequest) -> HttpResponse:
    last_loc = RandallLocation.objects.order_by("-timestamp")[:1].first()

    return render(request, "randall_index.html", context={"last_loc": last_loc})

@permission_required("common_models.book_randall", login_url='/accounts/login')
def book(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        form = RandallBookingForm()
        return render(request, "randall_book.html", context={"form": form})
    else:
        form = RandallBookingForm(request.POST)
        if form.is_valid():
            if not is_randall_available(form.cleaned_data["start"], form.cleaned_data["end"]):
                return render(request, "randall_book.html", context={"form": form, "error": "booked"})
            else:
                booking = form.save(commit=False)
                booking.user = request.user
                booking.save()
                DiscordChannel.send_to_backstage_updates_channels("@everyone - New booking submitted!\nTeam: " + booking.user.details.team.display_name + "\nStart: " + str(booking.start) + "\nEnd: " + str(booking.end))
                return redirect("/randall")
        else:
            return render(request, "randall_book.html", context={"form": form})