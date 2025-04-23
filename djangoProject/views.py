from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from events.models import Event
from registration.models import Ticket, RegistrationField, Registration
from django.contrib import messages

import secrets
import string

def generate_secure_password(length=12):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def home(request):
        """
        Handles the event registration process.
        """
        # Fetch all active events
        events = Event.objects.filter(is_active=True).prefetch_related("ticket_types", "custom_fields")

        if request.method == "POST":
            # Retrieve event_id from form POST data
            event_id = request.POST.get("event_id")

            if not event_id:
                messages.error(request, "Event ID is missing.")
                return redirect("home")  # Update namespace

            # Validate event existence
            try:
                selected_event = Event.objects.get(id=event_id, is_active=True)
            except Event.DoesNotExist:
                messages.error(request, "The selected event does not exist.")
                return redirect("home")  # Update namespace

            # Validate custom fields
            registration_data = {}
            fields = selected_event.custom_fields.all()
            for field in fields:
                field_value = request.POST.get(field.field_name, "").strip()
                if field.is_required and not field_value:
                    messages.error(request, f"'{field.field_name}' is required.")
                    return redirect("home")  # Update namespace
                registration_data[field.field_name] = field_value

            # Validate ticket selection
            ticket_id = request.POST.get("ticket_type")
            if not ticket_id:
                messages.error(request, "Please select a ticket.")
                return redirect("home")  # Update namespace

            try:
                ticket = Ticket.objects.get(id=ticket_id, event=selected_event)
            except Ticket.DoesNotExist:
                messages.error(request, "Invalid ticket selection.")
                return redirect("home")  # Update namespace
            CustomUser = get_user_model()

            # User data
            user_data = registration_data

            random_password = generate_secure_password()
            existing_user = CustomUser.objects.filter(email=user_data["Email"]).first()

            if existing_user:
                # Check if this user already has a registration for the selected event
                if Registration.objects.filter(event=selected_event, user=existing_user).exists():
                    messages.error(request, f"The user with email {user_data['Email']} has already registered for this event.")
                    return redirect("home")  # Update namespace


            else:
                # Create a new user if no existing user with the email is found
                new_user = CustomUser.objects.create_user(
                    username=random_password,
                    email=user_data["Email"],
                    first_name=user_data['First Name'],
                    last_name=user_data["Last Name"],
                    phone_number=user_data["Phone Number"],
                    title=user_data["Title"],
                    role="VISITOR",
                    password=random_password,  # Set the generated password
                )

                # Save the new user
                new_user.save()

                # Assign the user object for creating the registration
                existing_user = new_user
            # Create the registration
            Registration.objects.create(
                event=selected_event,
                user=new_user,
                ticket_type=ticket,
                registration_data=json.dumps(registration_data),
            )

            messages.success(request, f"Successfully registered for {selected_event.name}!")
            return redirect("home")

        # Render registration page with event data
        event_data = [
            {
                "id": event.id,
                "name": event.name,
                "logo" :event.logo,
                "description": event.description,
                "start_date": event.start_date.strftime("%b %d"),
                "end_date": event.end_date.strftime("%b %d"),
                "venue": event.venue.name if event.venue else "N/A",
                "category": event.category.name if event.category else "N/A",
                "tickets": [{"id": t.id, "name": t.name} for t in event.ticket_types.all()],
                "fields": [
                    {
                        "field_name": f.field_name,
                        "field_type": f.field_type,
                        "is_required": f.is_required,
                        "options": f.options.split(",") if f.options else [],
                    }
                    for f in event.custom_fields.all()
                ],
            }
            for event in events
        ]

        return render(request, "home.html", {"events": event_data})


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
