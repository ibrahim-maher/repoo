# system/analytics/reports.py
from registration.models import Registration
from events.models import Event

def generate_visitor_report(event_id):
    event = Event.objects.get(id=event_id)
    registrations = Registration.objects.filter(event=event)
    report = {
        'event': event.name,
        'total_registrations': registrations.count(),
        'attendees': [reg.user.username for reg in registrations]
    }
    return report