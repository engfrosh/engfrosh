from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
import json
from common_models.models import UserDetails, FroshRole
from django.core.serializers.json import DjangoJSONEncoder
from .forms import CheckInForm
from .consumers import CheckInConsumer

@staff_member_required(login_url='/accounts/login/')
def check_in_view(request: HttpRequest, id: int) -> HttpResponse:
    user = UserDetails.objects.filter(user=id).first()  # This is safe as user is a pk
    if user is None:
        return HttpResponse('Failed to find user!')
    if user.checked_in:
        return HttpResponse('User is already checked in!')
    user.checked_in = True

    location = request.user.username  # User name will be used as the location
    size = user.shirt_size
    groups = user.user.groups
    frosh_groups = FroshRole.objects.all()
    names = []
    for g in frosh_groups:
        names += [g.name]
    team = groups.exclude(name__in=names).first()
    if team is None:
        team = "None"
    else:
        team = team.name

    CheckInConsumer.notify_trigger(location, size, team)

    user.save()
    return redirect('/check-in/')


@staff_member_required(login_url='/accounts/login/')
def check_in_index(request: HttpRequest) -> HttpResponse:
    if request.GET.get('name', None) != None:
        form = CheckInForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            if name.isnumeric():
                results = UserDetails.objects.filter(user=int(name))
            else:
                results = UserDetails.objects.filter(name__icontains=name)
            data = results.values('name', 'user', 'shirt_size', 'checked_in')

            return render(request, "check_in.html", {'form': form, 'data': data})
        else:
            return render(request, "check_in.html", {'form': CheckInForm(), 'error': 'Invalid Name!'})
    else:
        return render(request, "check_in.html", {'form': CheckInForm()})


@staff_member_required(login_url='/accounts/login/')
def check_in_monitor(request: HttpRequest) -> HttpResponse:
    return render(request, "monitor.html")
