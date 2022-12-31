from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .forms import TicketForm, TicketCommentForm, TicketUpdateForm
from django.shortcuts import redirect
from common_models.models import Ticket, DiscordChannel
from management.email import send_email


@login_required(login_url='/accounts/login')
def create_ticket(request: HttpRequest):
    if request.method == 'GET':
        context = {'form': TicketForm()}
        return render(request, "create_ticket.html", context)
    elif request.method == 'POST':
        form = TicketForm(request.POST)
        if not form.is_valid():
            context = {'form': form}
            return render(request, "create_ticket.html", context)
        else:
            data = form.cleaned_data
            ticket = Ticket(title=data['title'], body=data['body'], user=request.user)
            ticket.save()
            DiscordChannel.send_to_updates_channels(
                f"""@here Ticket {ticket.id} has been created. """ +
                f"""{request.build_absolute_uri("/tickets/view/"+str(ticket.id))}""")
            return redirect('view/'+str(ticket.id))


def can_view_ticket(ticket: Ticket, user: User):
    if ticket.user == user:
        return True
    return user.is_staff


@login_required(login_url='/accounts/login')
def view_ticket(request: HttpRequest, id: int):
    ticket = Ticket.objects.filter(id=id).first()
    if ticket is None:
        return redirect('create_ticket')
    if not can_view_ticket(ticket, request.user):
        return redirect('create_ticket')
    context = {'ticket': ticket, 'comment_form': TicketCommentForm(),
               'update_form': TicketUpdateForm(initial=ticket.status)}
    return render(request, "view_ticket.html", context)


@login_required(login_url='/accounts/login')
def create_comment(request: HttpRequest, id: int):
    ticket = Ticket.objects.filter(id=id).first()
    if ticket is None:
        return redirect('create')
    if not can_view_ticket(ticket, request.user):
        return redirect('create')
    if request.method == 'POST':
        form = TicketCommentForm(request.POST)
        if not form.is_valid():
            return redirect('')
        data = form.cleaned_data
        ticket.create_comment(request.user, data['body'])
        if not request.user.is_staff:
            DiscordChannel.send_to_updates_channels(
                f"""@here Ticket {ticket.id} has a new comment. """ +
                f"""{request.build_absolute_uri("/tickets/view/"+str(ticket.id))}""")
        else:
            send_email(user=ticket.user, sender_email="noreply@engfrosh.com", subject="EngFrosh Ticket",
                       body_html="",
                       body_text="Your ticket has new comments, view them at " +
                                 f"""{request.build_absolute_uri("/tickets/view/"+str(ticket.id))}""")
        return redirect('/tickets/view/'+str(ticket.id))
    else:
        return HttpResponse('Invalid request!')


@login_required(login_url='/accounts/login')
@staff_member_required()
def ticket_action(request: HttpRequest, id: int):
    ticket = Ticket.objects.filter(id=id).first()
    if ticket is None:
        return redirect('create_ticket')
    if not can_view_ticket(ticket, request.user):
        return redirect('create_ticket')
    if request.method == 'POST':
        form = TicketUpdateForm(request.POST)
        if not form.is_valid():
            return redirect("/tickets/view/"+str(ticket.id))
        data = form.cleaned_data
        ticket.status = data['status']
        ticket.save()
        return redirect('/tickets/view/'+str(ticket.id))
    else:
        return HttpResponse('Invalid request!')
    pass


@login_required(login_url='/accounts/login')
@staff_member_required()
def view_all_tickets(request: HttpRequest):
    tickets = list(Ticket.objects.exclude(status=3).order_by('opened'))
    return render(request, 'view_tickets.html', {'tickets': tickets})
