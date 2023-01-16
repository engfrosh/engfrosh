from django.shortcuts import render
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

# This is hard coded because I'm lazy, it doesn't actual do anything important so this is fine
PASSWORD = "spiritstuffgoeshere"


@login_required(login_url='/accounts/login')
@staff_member_required()
def counter(request: HttpRequest):
    return render(request, "counter.html", {"password": PASSWORD, "hours": 16, "minutes": 0, "seconds": 0})
