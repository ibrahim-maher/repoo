from django.shortcuts import render, get_object_or_404
from ..models import Ticket
from django.contrib.auth.decorators import login_required

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    return render(request, 'registration/ticket.html', {'ticket': ticket})
