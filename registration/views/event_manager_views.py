from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from ..models import Ticket
from ..forms import TicketForm
from events.models import Event

@login_required
def manager_manage_ticket_types(request, event_id):
    # Ensure the user is an event manager
    if not request.user.is_event_manager:
        return HttpResponseForbidden("You don't have permission to manage ticket types.")

    # Ensure the event belongs to the event manager
    event = get_object_or_404(Event, id=event_id, created_by=request.user)

    if request.method == 'POST':
        form = TicketTypeForm(request.POST)
        if form.is_valid():
            ticket_type = form.save(commit=False)
            ticket_type.event = event
            ticket_type.created_by = request.user
            ticket_type.save()
            return redirect('registration:manager_manage_ticket_types', event_id=event.id)
    else:
        form = TicketTypeForm()

    ticket_types = TicketType.objects.filter(event=event)
    return render(request, 'registration/manager_manage_ticket_types.html', {
        'form': form, 'ticket_types': ticket_types, 'event': event
    })


@login_required
def manager_edit_ticket_type(request, event_id, ticket_type_id):
    # Ensure the user is an event manager
    if not request.user.is_event_manager:
        return HttpResponseForbidden("You don't have permission to edit ticket types.")

    # Ensure the event and ticket type belong to the event manager
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    ticket_type = get_object_or_404(TicketType, id=ticket_type_id, event=event)

    if request.method == 'POST':
        form = TicketTypeForm(request.POST, instance=ticket_type)
        if form.is_valid():
            form.save()
            return redirect('registration:manager_manage_ticket_types', event_id=event.id)
    else:
        form = TicketTypeForm(instance=ticket_type)

    return render(request, 'registration/manager_edit_ticket_type.html', {
        'form': form, 'ticket_type': ticket_type, 'event': event
    })


@login_required
def manager_delete_ticket_type(request, event_id, ticket_type_id):
    # Ensure the user is an event manager
    if not request.user.is_event_manager:
        return HttpResponseForbidden("You don't have permission to delete ticket types.")

    # Ensure the event and ticket type belong to the event manager
    event = get_object_or_404(Event, id=event_id, created_by=request.user)
    ticket_type = get_object_or_404(TicketType, id=ticket_type_id, event=event)

    if request.method == 'POST':
        ticket_type.delete()
        return redirect('registration:manager_manage_ticket_types', event_id=event.id)

    return render(request, 'registration/manager_delete_ticket_type.html', {
        'ticket_type': ticket_type, 'event': event
    })
