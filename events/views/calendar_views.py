# events/views/calendar_views.py
from django.shortcuts import render
from ..models import Event

def calendar_view(request):
    events = Event.objects.all()
    return render(request, 'events/event_calendar.html', {'events': events})