from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import permission_required
from common_models.models import UserDetails, FroshRole
from .forms import CheckInForm
from .consumers import CheckInConsumer


@permission_required("common_models.check_in")
def prc(request: HttpRequest, id: int) -> HttpResponse:
    user = UserDetails.objects.filter(user__id=id).first()  # This is safe as user is a pk
    if user is None:
        return HttpResponse('Failed to find user!')
    user.prc_completed = True
    user.save()
    return HttpResponse("User modified! You can close this window!")


@permission_required("common_models.check_in")
def contract(request: HttpRequest, id: int) -> HttpResponse:
    user = UserDetails.objects.filter(user__id=id).first()  # This is safe as user is a pk
    if user is None:
        return HttpResponse('Failed to find user!')
    user.contract = True
    user.save()
    return HttpResponse("User modified! You can close this window!")


@permission_required("common_models.check_in")
def brightspace(request: HttpRequest, id: int) -> HttpResponse:
    user = UserDetails.objects.filter(user__id=id).first()  # This is safe as user is a pk
    if user is None:
        return HttpResponse('Failed to find user!')
    user.brightspace_completed = True
    user.save()
    return HttpResponse("User modified! You can close this window!")


@permission_required("common_models.check_in")
def hardhat(request: HttpRequest, id: int) -> HttpResponse:
    user = UserDetails.objects.filter(user__id=id).first()  # This is safe as user is a pk
    if user is None:
        return HttpResponse('Failed to find user!')
    user.hardhat = True
    user.hardhat_paid = True
    user.save()
    return HttpResponse("User modified! You can close this window!")


@permission_required("common_models.check_in")
def rafting(request: HttpRequest, id: int) -> HttpResponse:
    user = UserDetails.objects.filter(user__id=id).first()  # This is safe as user is a pk
    if user is None:
        return HttpResponse('Failed to find user!')
    user.rafting = True
    user.rafting_paid = True
    user.save()
    return HttpResponse("User modified! You can close this window!")


@permission_required("common_models.check_in")
def waiver(request: HttpRequest, id: int) -> HttpResponse:
    user = UserDetails.objects.filter(user__id=id).first()  # This is safe as user is a pk
    if user is None:
        return HttpResponse('Failed to find user!')
    user.waiver_completed = True
    user.save()
    return HttpResponse("User modified! You can close this window!")


@permission_required("common_models.check_in")
def wt_waiver(request: HttpRequest, id: int) -> HttpResponse:
    user = UserDetails.objects.filter(user__id=id).first()  # This is safe as user is a pk
    if user is None:
        return HttpResponse('Failed to find user!')
    user.wt_waiver_completed = True
    user.save()
    return HttpResponse("User modified! You can close this window!")


@permission_required("common_models.check_in")
def check_in_view(request: HttpRequest, id: int) -> HttpResponse:
    user = UserDetails.objects.filter(user__id=id).first()  # This is safe as user is a pk
    if user is None:
        return HttpResponse('Failed to find user!')
    if user.checked_in:
        return HttpResponse('User is already checked in!')
    user.checked_in = True

    location = request.user.username  # User name will be used as the location
    size = user.shirt_size
    ssize = user.sweater_size
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
    CheckInConsumer.notify_trigger(location, size, ssize, team, user.name)

    user.save()
    return render(request, "check_in.html", {'form': CheckInForm(), 'data': [user]})


@permission_required("common_models.check_in")
def check_in_index(request: HttpRequest) -> HttpResponse:
    if request.GET.get('name', None) is not None:
        form = CheckInForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            if name.isnumeric():
                results = UserDetails.objects.filter(user=int(name))
            else:
                results = UserDetails.objects.filter(name__icontains=name)
            return render(request, "check_in.html", {'form': form, 'data': results})
        else:
            return render(request, "check_in.html", {'form': CheckInForm(), 'error': 'Invalid Name!'})
    else:
        return render(request, "check_in.html", {'form': CheckInForm()})


@permission_required("common_models.check_in")
def check_in_monitor(request: HttpRequest) -> HttpResponse:
    return render(request, "monitor.html")
