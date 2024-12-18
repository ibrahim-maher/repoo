from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from events.models import Event
from registration.models import Ticket, RegistrationField, Registration


def home(request):
    events = Event.objects.filter(is_active=True)  # Filter to only get active events
    event_data = []

    for event in events:
        tickets = event.ticket_types.all()

        event_info = {
            'id': event.id,
            "name": event.name,
            "description": event.description,
            "start_date": event.start_date.strftime("%b %d"),
            "end_date": event.end_date.strftime("%b %d"),
            "venue": event.venue.name if event.venue else "N/A",
            "category": event.category.name if event.category else "N/A",
            "tickets": [],
            "fields": []
        }

        # Fetch Custom Registration Fields
        fields = RegistrationField.objects.filter(event=event)
        for field in fields:
            field_info = {
                "field_name": field.field_name,
                "field_type": field.field_type,
                "is_required": field.is_required,
                "options": field.options.split(',') if field.options else []
            }
            event_info["fields"].append(field_info)

        # Fetch Tickets
        for ticket in tickets:
            ticket_info = {
                "id": ticket.id,
                "name": ticket.name,

            }
            event_info["tickets"].append(ticket_info)

        event_data.append(event_info)
        break
    return render(request, 'home.html', {
        'events': event_data,
    })


def admins(request):
    return render(request, 'admins.html')


@require_POST
def register_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id)

        # Validate ticket selection
        ticket_id = request.POST.get('ticket_type')
        if not ticket_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Please select a ticket type'
            })

        ticket = Ticket.objects.get(id=ticket_id)

        # Check ticket availability
        if ticket.capacity <= 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Ticket type sold out'
            })

        # Collect custom field data
        custom_fields = RegistrationField.objects.filter(event=event)
        registration_data = {}

        for field in custom_fields:
            field_value = request.POST.get(f'field_{field.id}', '')

            # Validate required fields
            if field.is_required and not field_value:
                return JsonResponse({
                    'status': 'error',
                    'message': f'{field.field_name} is required'
                })

            registration_data[field.field_name] = field_value

        # Create registration
        registration = Registration.objects.create(
            event=event,
            user=request.user,
            ticket_type=ticket,
            registration_data=json.dumps(registration_data)
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Registration successful',
        })

    except Event.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Event not found'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })
