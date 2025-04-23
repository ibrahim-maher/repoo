from django.shortcuts import render
from ..models import Event, Venue, Category

def filter_events(request):
    category = request.GET.get('category')
    venue = request.GET.get('venue')
    events = Event.objects.all()

    if category:
        events = events.filter(category__name=category)
    if venue:
        events = events.filter(venue__name=venue)

    return render(request, 'events/event_list.html', {'events': events})