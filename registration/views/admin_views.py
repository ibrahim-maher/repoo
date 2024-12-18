import csv
import json
from datetime import datetime, timedelta

from django.db import transaction
from django.shortcuts import redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models.signals import post_save
from django.dispatch import receiver

from badges.models import BadgeTemplate, BadgeContent
from users.forms import CustomUserCreationForm
from users.models import RoleChoices, CustomUser
from ..models import Ticket, RegistrationField, Registration, QRCode
from ..forms import TicketForm, RegistrationFieldForm, DynamicRegistrationForm
from events.models import Event
from django.contrib.auth import get_user_model
from django.db.models import Prefetch



def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'


def is_event_manager(user):
    return user.is_authenticated and user.role == 'EVENT_MANAGER'


@login_required
def manage_tickets(request, event_id):
    """
    Admin can manage tickets (add, update, delete).
    """
    if not is_admin(request.user) and not is_event_manager(request.user):
        return HttpResponseForbidden("You don't have permission to manage tickets.")

    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.event = event
            ticket.created_by = request.user
            ticket.save()
            return redirect('registration:admin_manage_tickets', event_id=event.id)
    else:
        form = TicketForm()

    tickets = Ticket.objects.filter(event=event)
    return render(request, 'registration/admin_manage_tickets.html', {
        'form': form, 'tickets': tickets, 'event': event
    })


@login_required
def edit_ticket(request, ticket_id):
    """
    Admin can edit ticket details.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    event = ticket.event

    if not is_admin(request.user) and not is_event_manager(request.user):
        return HttpResponseForbidden("You don't have permission to edit tickets.")

    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect('registration:admin_manage_tickets', event_id=event.id)
    else:
        form = TicketForm(instance=ticket)

    return render(request, 'registration/admin_edit_ticket.html', {
        'form': form, 'ticket': ticket, 'event': event
    })


@login_required
def delete_ticket(request, ticket_id):
    """
    Admin can delete a ticket.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    event = ticket.event

    if not is_admin(request.user) and not is_event_manager(request.user):
        return HttpResponseForbidden("You don't have permission to delete tickets.")

    if request.method == 'POST':
        ticket.delete()
        return redirect('registration:admin_manage_tickets', event_id=event.id)

    return render(request, 'registration/admin_delete_ticket.html', {
        'ticket': ticket, 'event': event
    })


@login_required
def list_tickets(request):
    """
    Admin can view all ticket types and search them by event name or ticket type.
    """
    if not is_admin(request.user) and not is_event_manager(request.user):
        return HttpResponseForbidden("You don't have permission to view tickets.")

    search_query = request.GET.get('search', '').strip()
    tickets = Ticket.objects.select_related('event').all()

    if search_query:
        tickets = tickets.filter(
            Q(name__icontains=search_query) | Q(event__name__icontains=search_query)
        )

    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    rows = [
        {
            "cells": [
                ticket.name,

                ticket.event.name if ticket.event else "N/A",
            ],
            "actions": [
                {
                    "url": reverse("registration:edit_ticket", args=[ticket.id]),
                    "class": "warning",
                    "icon": "la la-edit",
                    "label": "Edit",
                },
                {
                    "url": reverse("registration:delete_ticket", args=[ticket.id]),
                    "class": "danger",
                    "icon": "la la-trash",
                    "label": "Delete",
                },
            ],
        }
        for ticket in page_obj
    ]

    context = {
        "heading": "Ticket Types",
        "table_heading": "All Ticket Types",
        "columns": ["Name", "Event"],
        "rows": rows,
        "show_create_button": True,
        "create_action": reverse("registration:create_ticket"),
        "create_button_label": "Create Ticket",
        "search_action": reverse("registration:admin_list_tickets"),
        "search_placeholder": "Search Ticket Types...",
        "search_query": search_query,
        "paginator": paginator,
        "page_obj": page_obj,
    }

    return render(request, 'registration/admin_ticket_list.html', context)


@login_required
def create_ticket(request):
    """
    Allows admin to create a new ticket for a specific event.
    """
    if not is_admin(request.user) and not is_event_manager(request.user):
        return HttpResponseForbidden("You don't have permission to create tickets.")
  
    events = Event.objects.all()

    if request.method == 'POST':
        event_id = request.POST.get('event')
        selected_event = get_object_or_404(Event, id=event_id)

        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.event = selected_event
            ticket.created_by = request.user
            ticket.save()
            return redirect('registration:admin_list_tickets')
    else:
        form = TicketForm()

    return render(request, 'registration/create_ticket.html', {
        'form': form,
        'events': events
    })


@login_required
@login_required
def list_registrations(request):
    """
    Admin can view all registrations, search, sort, and filter them.
    """
    if not is_admin(request.user) and not is_event_manager(request.user):
        return HttpResponseForbidden("You don't have permission to view registrations.")

    # Check if sorting is enabled
    show_sorting = request.GET.get('show_sorting', 'true') == 'true'

    # Get all filter parameters
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'registered_at')
    order = request.GET.get('order', 'asc')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    action = request.GET.get('action', '')
    event_id = request.GET.get('event', '')
    ticket_type_id = request.GET.get('ticket_type', '')

    # Determine valid sort fields
    valid_sort_fields = ['registered_at', 'user__first_name', 'user__username', 'event__name']
    if sort_by not in valid_sort_fields:
        sort_by = 'registered_at'
    sort_field = sort_by if order == 'asc' else f"-{sort_by}"

    # Fetch registrations with sorting and filtering
    registrations = Registration.objects.all()

    # Apply event filter
    if event_id:
        registrations = registrations.filter(event_id=event_id)

    # Apply ticket type filter
    if ticket_type_id:
        registrations = registrations.filter(ticket_type_id=ticket_type_id)

    # Apply date filters
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            registrations = registrations.filter(registered_at__gte=date_from)
        except ValueError:
            pass

    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire end date
            date_to = date_to + timedelta(days=1)
            registrations = registrations.filter(registered_at__lt=date_to)
        except ValueError:
            pass


    # Apply search filter
    if search_query:
        registrations = registrations.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(event__name__icontains=search_query)
        )

    # Apply sorting

    #if is_event_manager:
   #     events = request.user.assigned_events.all()
   #     registrations = Registration.objects.filter(event__in=events)

    #else:
    registrations = registrations.order_by(sort_field)


    # Fetch all events and ticket types for the filter dropdowns
    #if is_event_manager:
    #    events = request.user.assigned_events.all().order_by('name')
    #else:
    events = Event.objects.all().order_by('name')

    ticket_types = Ticket.objects.all().order_by('name')

    # Pagination
    paginator = Paginator(registrations, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    rows = [
        {
            "cells": [
                registration.user.username,
                f"{registration.user.first_name} {registration.user.last_name}",
                registration.user.email,
                registration.user.title,
                registration.user.phone_number,
                registration.registered_at.strftime("%Y-%m-%d %H:%M"),
                registration.event.name,
                registration.ticket_type.name if registration.ticket_type else "N/A",
            ],
            "actions": [
                {
                    "url": reverse("registration:registration_detail", args=[registration.id]),
                    "class": "info",
                    "icon": "la la-eye",
                    "label": "View",
                },
                {
                    "url": reverse("registration:registration_edit", args=[registration.id]),
                    "class": "warning",
                    "icon": "la la-edit",
                    "label": "Edit",
                },
                {
                    "url": reverse("registration:registration_delete", args=[registration.id]),
                    "class": "danger",
                    "icon": "la la-trash",
                    "label": "Delete",
                },
            ],
        }
        for registration in page_obj
    ]

    context = {
        "heading": "Registrations",
        "table_heading": "Registration List",
        "columns": ["Username", "Name", "Email", "Title", "Phone", "Date", "Event", "Ticket"],
        "rows": rows,
        "show_create_button": True,
        "show_filters": True,
        "create_action": reverse("registration:create_registration"),
        "create_button_label": "Create New Registration",
        "search_action": reverse("registration:admin_list_registrations"),
        "search_placeholder": "Search Registrations...",
        "search_query": search_query,
        "paginator": paginator,
        "page_obj": page_obj,
        "events": events,
        "ticket_types": ticket_types,
        "selected_event": event_id,
        "selected_ticket_type": ticket_type_id,
        "show_export_button": True,
        "export_action": reverse("registration:export_registrations_csv"),
        "export_button_label": "Export CSV",
        "show_import_button": True,
        "import_action": reverse("registration:import_registrations_csv"),
        "import_button_label": "Import CSV",
        "sort_by": sort_by,
        "order": order,
        "show_sorting": show_sorting,
    }

    return render(request, "registration/admin_registration_list.html", context)

import csv


def export_registrations_csv(request):
    if not request.user.is_admin and not request.user.is_event_manager:
        return HttpResponseForbidden("You don't have permission to export registrations.")

    registrations = Registration.objects.select_related('user', 'event', 'ticket_type').all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="registrations.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Username",
        "First Name",
        "Last Name",
        "Email",
        "Title",
        "Phone",
        "Registration Date",
        "Event Name",
        "Ticket Type Name",
        "Registration Data"
    ])

    for registration in registrations:
        registration_data = registration.get_registration_data()  # Deserialize registration_data field
        writer.writerow([
            registration.user.username,
            registration.user.first_name,
            registration.user.last_name,
            registration.user.email,
            registration.user.title,
            registration.user.phone_number if registration.user.phone_number else "N/A",
            registration.registered_at.strftime("%Y-%m-%d %H:%M:%S"),
            registration.event.name,
            registration.ticket_type.name if registration.ticket_type else "N/A",
            json.dumps(registration_data),  # Serialize registration data back to JSON string
        ])

    return response


def import_registrations_csv(request):
    if not request.user.is_admin and not request.user.is_event_manager:
        return HttpResponseForbidden("You don't have permission to import registrations.")

    if request.method == 'POST' and 'csv_file' in request.FILES:
        file = request.FILES['csv_file']
        try:
            reader = csv.reader(file.read().decode('utf-8').splitlines())
            next(reader)

            for row in reader:
                try:
                    username, first_name, last_name, email, title, phone, registered_at, event_name, ticket_type_name, registration_data = row
                except ValueError:
                    messages.error(request, "CSV row does not have the correct number of fields.")
                    continue

                # Create or update the user
                user, created = CustomUser.objects.get_or_create(username=username, defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'title': title,
                    'phone_number': phone,
                    'role': RoleChoices.VISITOR,
                })

                # Lookup the event
                try:
                    event = Event.objects.get(name=event_name)
                except Event.DoesNotExist:
                    messages.error(request, f"Event '{event_name}' not found.")
                    continue

                # Lookup the ticket type
                ticket_type = Ticket.objects.filter(name=ticket_type_name, event=event).first()

                # Create the registration
                Registration.objects.create(
                    user=user,
                    event=event,
                    ticket_type=ticket_type,
                )

            messages.success(request, "Registrations imported successfully.")
        except Exception as e:
            messages.error(request, f"Error importing CSV: {e}")

    return redirect("registration:admin_list_registrations")


@login_required
def export_tickets_csv(request):
    """
    Export ticket types to a CSV file.
    """
    if not is_admin(request.user) and not is_event_manager(request.user):
        return HttpResponseForbidden("You don't have permission to export tickets.")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ticket_types.csv"'

    writer = csv.writer(response)
    writer.writerow(['Event Name', 'Ticket Type', 'Price', 'Capacity'])

    tickets = Ticket.objects.all()
    for ticket in tickets:
        writer.writerow([ticket.event.name, ticket.name, ticket.price, ticket.capacity])

    return response


User = get_user_model()



import secrets
import string

def generate_secure_password(length=12):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@login_required
def create_registration_view(request):
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
            return redirect("registration:create_registration")  # Update namespace

        # Validate event existence
        try:
            selected_event = Event.objects.get(id=event_id, is_active=True)
        except Event.DoesNotExist:
            messages.error(request, "The selected event does not exist.")
            return redirect("registration:create_registration")  # Update namespace

        # Validate custom fields
        registration_data = {}
        fields = selected_event.custom_fields.all()
        for field in fields:
            field_value = request.POST.get(field.field_name, "").strip()
            if field.is_required and not field_value:
                messages.error(request, f"'{field.field_name}' is required.")
                return redirect("registration:create_registration")  # Update namespace
            registration_data[field.field_name] = field_value

        # Validate ticket selection
        ticket_id = request.POST.get("ticket_type")
        if not ticket_id:
            messages.error(request, "Please select a ticket.")
            return redirect("registration:create_registration")  # Update namespace

        try:
            ticket = Ticket.objects.get(id=ticket_id, event=selected_event)
        except Ticket.DoesNotExist:
            messages.error(request, "Invalid ticket selection.")
            return redirect("registration:create_registration")  # Update namespace
        CustomUser = get_user_model()

        # User data
        user_data=registration_data
        user_data = {
            "username": "visitor_user",
            "Email": "i.qezisin@gmail.com",
            "First_name": "dvsdvsds",
            "Last_name": "dfvcsdvsdv",
            "Phone Number": "0114556622",
            "Title": "Visitor Title Example",
            "role": "VISITOR",  # Explicitly set VISITOR role
        }
        random_password = generate_secure_password()

        # Create the user
        new_user = CustomUser.objects.create_user(
            username=random_password,
            email=user_data["Email"],
            first_name=user_data["First_name"],
            last_name=user_data["Last_name"],
            phone_number=user_data["Phone Number"],
            title=user_data["Title"],
            role="VISITOR",
            password=random_password,  # Set the generated password
        )


        # Save the user
        new_user.save()
        # Create the registration
        Registration.objects.create(
            event=selected_event,
            user=new_user,
            ticket_type=ticket,
            registration_data=json.dumps(registration_data),
        )

        messages.success(request, f"Successfully registered for {selected_event.name}!")
        return redirect("registration:create_registration")

    # Render registration page with event data
    event_data = [
        {
            "id": event.id,
            "name": event.name,
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

    return render(request, "registration/create_registration.html", {"events": event_data})


def search_user_view(request):
    """
    Search for users by phone, email, or name, filtering only visitors.
    """
    if request.method == "POST":
        phone = request.POST.get("search_phone", "").strip()
        email = request.POST.get("search_email", "").strip()
        name = request.POST.get("search_name", "").strip()

        users = CustomUser.objects.filter(role=RoleChoices.VISITOR)  # Filter only Visitors

        if phone:
            users = users.filter(phone_number__icontains=phone)
        if email:
            users = users.filter(email__icontains=email)
        if name:
            users = users.filter(first_name__icontains=name) | users.filter(last_name__icontains=name)

        user_data = [
            {"id": user.id, "first_name": user.first_name, "last_name": user.last_name, "email": user.email}
            for user in users
        ]
        return JsonResponse({"users": user_data})
    return JsonResponse({"error": "Invalid request method."}, status=400)


def fetch_registration_fields(request, event_id):
    """
    Fetch dynamic fields and ticket types for the selected event.
    """
    if request.method == "GET":
        event = get_object_or_404(Event, id=event_id)
        fields = event.custom_fields.values("field_name", "field_type", "is_required", "options")
        ticket_types = event.tickets.values("id", "name", "price")
        return JsonResponse({"fields": list(fields), "tickets": list(ticket_types)})
    return JsonResponse({"error": "Invalid request method."}, status=400)


def fetch_ticket_types(request, event_id):
    event = Event.objects.get(id=event_id)
    ticket_types = Ticket.objects.filter(event=event)
    ticket_data = [{'id': ticket.id, 'name': ticket.name, 'price': ticket.price} for ticket in ticket_types]
    return JsonResponse(ticket_data, safe=False)


@login_required
def manage_registration_fields(request, event_id):
    """
    Admin can manage registration fields (add, delete).
    """
    if not is_admin(request.user) and not is_event_manager(request.user):
        return HttpResponseForbidden("You don't have permission to manage registration fields.")

    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = RegistrationFieldForm(request.POST)
        if form.is_valid():
            field = form.save(commit=False)
            field.event = event
            field.created_by = request.user
            field.save()
            return redirect('registration:admin_manage_registration_fields', event_id=event.id)
    else:
        form = RegistrationFieldForm()

    fields = RegistrationField.objects.filter(event=event)
    return render(request, 'registration/admin_manage_registration_fields.html', {
        'form': form, 'fields': fields, 'event': event
    })


@login_required
def delete_registration_field(request, event_id, field_id):
    """
    Admin can delete a registration field.
    """
    if not is_admin(request.user) and not is_event_manager(request.user):
        return HttpResponseForbidden("You don't have permission to delete registration fields.")

    event = get_object_or_404(Event, id=event_id)
    field = get_object_or_404(RegistrationField, id=field_id, event=event)

    if request.method == 'POST':
        field.delete()
        return redirect('registration:admin_manage_registration_fields', event_id=event.id)

    return render(request, 'registration/admin_delete_registration_field.html', {
        'field': field, 'event': event
    })


def registration_detail(request, registration_id):
    """
    View the details of a specific registration along with user details, QR code, and badge preview.
    """
    # Fetch the registration and associated user
    registration = get_object_or_404(Registration, id=registration_id)

    # Check permissions: Only admins, event managers, and the user who created the registration can view it
    if not (request.user.is_admin or request.user.is_event_manager or registration.user == request.user):
        return HttpResponseForbidden("You don't have permission to view this registration.")

    # Fetch custom fields for the event
    registration_fields = RegistrationField.objects.filter(event=registration.event)

    # Fetch the QR code for the registration
    qr_code = None


    # Fetch badge template and badge data
    badge_template = BadgeTemplate.objects.filter(event=registration.event).first()
    badge_data = {}
    badge_contents = []

    if badge_template:
        badge_contents = BadgeContent.objects.filter(template=badge_template)
        for content in badge_contents:
            if content.field_name == 'qr_code__qr_image':
                # Get QR Code for registration
                try:
                    qr_code_obj = QRCode.objects.get(registration=registration)
                    badge_data[content.field_name] = qr_code_obj.qr_image
                except QRCode.DoesNotExist:
                    badge_data[content.field_name] = None
            else:
                # Get field value for other badge contents
                badge_data[content.field_name] = content.get_field_value(registration)

    # Prepare registration data (dynamic fields) as a dictionary
    registration_data = registration.get_registration_data()

    context = {
        "registration": registration,
        "user_in_args": registration.user,
        "registration_data": registration_data,
        "registration_fields": registration_fields,
        "qr_code": qr_code,
        "badge_data": badge_data,
        "badge_template": badge_template,
        "badge_contents": badge_contents,
    }

    return render(request, "registration/registration_detail.html", context)


@login_required
def registration_edit(request, registration_id):
    """
    Edit the details of a specific registration.
    """
    registration = get_object_or_404(Registration, id=registration_id)

    # Check permissions: Only admins, event managers, and the user who created the registration can edit it
    if not (request.user.is_admin or request.user.is_event_manager or registration.user == request.user):
        return HttpResponseForbidden("You don't have permission to edit this registration.")

    event = registration.event

    if request.method == "POST":
        form = DynamicRegistrationForm(event=event, data=request.POST, initial=registration.get_registration_data())
        if form.is_valid():
            registration_data = form.cleaned_data

            # Update ticket type if provided
            ticket_type_id = request.POST.get("ticket_type")
            if ticket_type_id:
                ticket_type = get_object_or_404(Ticket, id=ticket_type_id, event=event)
                registration.ticket_type = ticket_type

            # Save registration data
            registration.set_registration_data(registration_data)
            registration.save()

            return redirect("registration:registration_detail", registration_id=registration.id)
    else:
        form = DynamicRegistrationForm(event=event, initial=registration.get_registration_data())

    context = {
        "registration": registration,
        "form": form,
        "event": event,
    }
    return render(request, "registration/registration_edit.html", context)


def registration_delete(request, registration_id):
    """
    Deletes a specific registration.
    """
    registration = get_object_or_404(Registration, id=registration_id)

    # Check permissions: Only admins, event managers, or the user who created the registration can delete it
    if not (request.user.is_admin or request.user.is_event_manager or registration.user == request.user):
        return HttpResponseForbidden("You don't have permission to delete this registration.")

    if request.method == "POST":
        registration.delete()
        return redirect("registration:admin_list_registrations")  # Redirect to the list of registrations after deletion

    context = {
        "registration": registration,
    }
    return render(request, "registration/registration_delete.html", context)


@login_required
def fetch_ticket_types(request, event_id):
    """
    Fetch ticket types for a specific event.
    """
    # Check permissions
    if not (is_admin(request.user) or is_event_manager(request.user)):
        return JsonResponse({"error": "Permission denied"}, status=403)

    event = get_object_or_404(Event, id=event_id)
    tickets = Ticket.objects.filter(event=event).values(
        "id", "name", "price", "capacity"
    )
    return JsonResponse(list(tickets), safe=False)


@login_required
def fetch_registration_fields(request, event_id):
    """
    Fetch registration fields for a specific event.
    """
    # Check permissions
    if not (is_admin(request.user) or is_event_manager(request.user)):
        return JsonResponse({"error": "Permission denied"}, status=403)

    event = get_object_or_404(Event, id=event_id)
    fields = RegistrationField.objects.filter(event=event).values(
        "field_name", "field_type", "is_required", "options"
    )
    return JsonResponse(list(fields), safe=False)


@receiver(post_save, sender=Registration)
def create_qr_code_for_registration(sender, instance, created, **kwargs):
    """
    Generate a QR code for a new registration.
    """
    if created:
        # Delay the QR code generation until after the transaction is committed
        transaction.on_commit(lambda: _generate_and_save_qr_code(instance))


def _generate_and_save_qr_code(registration):
    """
    Helper function to generate and save a QR code for a registration.
    """
    qr_code = QRCode(registration=registration, ticket=registration.ticket_type)
    qr_code.generate_qr_code()
    qr_code.save()


def display_qr_code(request, registration_id):
    """
    Display the QR code for a specific registration.
    """
    registration = get_object_or_404(Registration, id=registration_id)
    qr_code = get_object_or_404(QRCode, registration=registration)
    return render(request, "registration/qr_code.html", {"qr_code": qr_code})


def download_qr_code(request, registration_id):
    """
    Download the QR code for a specific registration.
    """
    registration = get_object_or_404(Registration, id=registration_id)
    qr_code = get_object_or_404(QRCode, registration=registration)

    if not qr_code.qr_image:
        return HttpResponse("QR code not found", status=404)

    # Read and return the QR image file
    with qr_code.qr_image.open("rb") as f:
        response = HttpResponse(f.read(), content_type="image/png")
        response["Content-Disposition"] = f"attachment; filename=qr_{registration.id}.png"
        return response


def get_registration_badge(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)
    badge_template = BadgeTemplate.objects.filter(event=registration.event).first()

    if not badge_template:
        return HttpResponse("Badge template not found for the associated event.", status=404)

    badge_contents = BadgeContent.objects.filter(template=badge_template)
    badge_data = {}
    for content in badge_contents:
        if content.field_name == 'registration__qr_code':
            badge_data[content.field_name] = content.get_qr_code_image_path(registration)
        else:
            badge_data[content.field_name] = content.get_field_value(registration)



    return render(request, "registration/registration_badge.html", {
        "registration": registration,
        "badge_template": badge_template,
        "badge_data": badge_data,
        "badge_contents": badge_contents,
    })




