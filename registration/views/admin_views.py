import csv
import json
import json
import base64
from datetime import datetime, timedelta
from io import BytesIO

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.middleware.csrf import get_token
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
        "columns": ["number","Name", "Event"],
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
            Q(user__phone_number__icontains=search_query) |  # Added phone
            Q(user__title__icontains=search_query) |  # Added title
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
            "id": registration.id,  # Add this line to include registration ID
            "cells": [
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
                {
                    "url": reverse("registration:print_single_badge", args=[registration.id]),
                    "class": "primary",
                    "icon": "la la-id-card",
                    "label": "Print Badge",
                },
            ],
        }
        for registration in page_obj
    ]

    context = {
        "heading": "Registrations",
        "table_heading": "Registration List",
        "columns": [ "number","Name", "Email", "Title", "Phone", "Date", "Event", "Ticket"],
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


def print_single_badge(request, registration_id):
    """
    Generate and return a printable badge HTML page for a single registration.
    """
    try:
        # Get registration and related objects
        registration = get_object_or_404(Registration, id=registration_id)
        badge_template = BadgeTemplate.objects.filter(
            ticket__event=registration.event
        ).first()

        if not badge_template:
            error_html = f"""
            <html>
                <head>
                    <title>Badge Template Not Found</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .error-container {{ 
                            max-width: 600px; 
                            margin: 0 auto; 
                            padding: 20px; 
                            border: 1px solid #ddd; 
                            border-radius: 5px; 
                        }}
                        h2 {{ color: #d9534f; }}
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <h2>Badge Template Not Found</h2>
                        <p>No badge template has been created for event: <strong>{registration.event.name}</strong></p>
                    </div>
                </body>
            </html>
            """
            return HttpResponse(error_html, status=404)

        badge_contents = badge_template.contents.all()

        # Initialize image parameters
        DPI = 300
        width_px = int(float(badge_template.width) * DPI / 2.54)
        height_px = int(float(badge_template.height) * DPI / 2.54)

        # Create base image
        image = Image.new('RGB', (width_px, height_px), 'white')
        draw = ImageDraw.Draw(image)

        # Helper functions
        def cm_to_pixels(cm):
            return int(float(cm) * DPI / 2.54)

        def get_font(font_family, size_pt, is_bold, is_italic):
            try:
                size_px = int(size_pt * DPI / 72)
                # Default to Arial if font not found
                return ImageFont.truetype('Arial', size_px)
            except:
                return ImageFont.load_default()

        # Add background image if exists
        if badge_template.background_image:
            try:
                with default_storage.open(badge_template.background_image.path) as f:
                    background = Image.open(f)
                    background = background.resize((width_px, height_px), Image.Resampling.LANCZOS)
                    image.paste(background, (0, 0))
            except Exception as e:
                print(f"Error loading background image: {e}")

        # Process each badge content field
        for content in badge_contents:
            x = cm_to_pixels(content.position_x)
            y = cm_to_pixels(content.position_y)

            if content.field_name == 'registration__qr_code':
                try:
                    qr_code = registration.qr_code
                    if qr_code and qr_code.qr_image:
                        with default_storage.open(qr_code.qr_image.name) as f:
                            qr_image = Image.open(f)
                            qr_size = cm_to_pixels(3)  # 3cm QR code
                            qr_image = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
                            image.paste(qr_image, (x, y))

                            # Add registration ID below QR code
                            id_font = get_font('Arial', 10, False, False)
                            id_text = str(registration.id)
                            text_bbox = draw.textbbox((0, 0), id_text, font=id_font)
                            text_width = text_bbox[2] - text_bbox[0]
                            draw.text(
                                (x + (qr_size - text_width) // 2, y + qr_size + 5),
                                id_text,
                                font=id_font,
                                fill='black'
                            )
                except Exception as e:
                    print(f"Error processing QR code: {e}")
                continue

            # Process text fields
            try:
                field_value = content.get_field_value(registration)
                if field_value:
                    font = get_font(
                        content.font_family,
                        content.font_size,
                        content.is_bold,
                        content.is_italic
                    )
                    draw.text(
                        (x, y),
                        str(field_value),
                        font=font,
                        fill=content.font_color
                    )
            except Exception as e:
                print(f"Error processing field {content.field_name}: {e}")

        # Save image to BytesIO
        img_io = BytesIO()
        image.save(img_io, format='PNG', dpi=(DPI, DPI))
        img_io.seek(0)

        # Create HTML response
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Print Badge - {registration.user.get_full_name()}</title>
                <style>
                    @page {{
                        size: {badge_template.width}cm {badge_template.height}cm;
                        margin: 0;
                    }}
                    body {{
                        margin: 0;
                        padding: 0;
                        width: {badge_template.width}cm;
                        height: {badge_template.height}cm;
                    }}
                    img {{
                        width: 100%;
                        height: 100%;
                        object-fit: contain;
                    }}
                    @media print {{
                        body {{
                            print-color-adjust: exact;
                            -webkit-print-color-adjust: exact;
                        }}
                    }}
                </style>
                <script>
                    window.onload = function() {{
                        window.print();
                        setTimeout(function() {{
                            window.close();
                        }}, 500);
                    }};
                </script>
            </head>
            <body>
                <img src="data:image/png;base64,{img_io.getvalue().hex()}" 
                     alt="Badge for {registration.user.get_full_name()}">
            </body>
        </html>
        """

        return HttpResponse(html_content)

    except Exception as e:
        error_html = f"""
        <html>
            <head>
                <title>Error Generating Badge</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .error-container {{ 
                        max-width: 600px; 
                        margin: 0 auto; 
                        padding: 20px; 
                        border: 1px solid #ddd; 
                        border-radius: 5px; 
                    }}
                    h2 {{ color: #d9534f; }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <h2>Error Generating Badge</h2>
                    <p>An error occurred while generating the badge: <strong>{str(e)}</strong></p>
                </div>
            </body>
        </html>
        """
        return HttpResponse(error_html, status=500)

def generate_badge_html(registration, badge_template, badge_data, badge_contents):
    """Generate standalone HTML for the badge that can be printed directly"""

    # Get background image URL if it exists
    background_image_url = badge_template.background_image.url if badge_template.background_image else None

    # Start building the HTML
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Registration Badge - {registration.user.get_full_name()}</title>
            <style>
                @page {{
                    size: {badge_template.width}cm {badge_template.height}cm;
                    margin: 0;
                }}
                body {{
                    margin: 0;
                    padding: 0;
                    width: {badge_template.width}cm;
                    height: {badge_template.height}cm;
                    position: relative;
                    background-color: white;
                }}
        """

    # Add background image if exists
    if background_image_url:
        html += f"""
                .badge-background {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-image: url('{background_image_url}');
                    background-size: cover;
                    background-position: center;
                    z-index: 0;
                }}
            """

    html += """
            </style>
        </head>
        <body>
        """

    # Add background div if needed
    if background_image_url:
        html += '<div class="badge-background"></div>'

    # Add each field from badge_data
    for field_name, field_value in badge_data.items():
        # Get the corresponding content object to fetch positioning and styling
        content = next((c for c in badge_contents if c.field_name == field_name), None)
        if not content:
            continue

        # Get position and styling
        position_x = content.position_x
        position_y = content.position_y
        font_size = content.font_size
        font_family = content.font_family
        font_color = content.font_color
        is_bold = content.is_bold
        is_italic = content.is_italic

        # Special handling for QR code
        if field_name == 'qr_code__qr_image':
            html += f"""
                <div style="position: absolute; top: {position_y}cm; left: {position_x}cm; z-index: 1;">
                    <div style="position: relative; display: inline-block;">
                        <img src="{field_value.url}" style="width: 3cm; height: 3cm;" alt="QR Code">
                        <div style="position: absolute;
                                    bottom: -0.2cm;
                                    left: 50%;
                                    transform: translateX(-50%);
                                    text-align: center;
                                    font-size: 10pt;
                                    color: black;
                                    background-color: rgba(255, 255, 255, 0.8);
                                    padding: 2px 5px;
                                    width: 100%;
                                    box-sizing: border-box;">
                            {registration.id}
                        </div>
                    </div>
                </div>
                """
        else:
            # Regular text field
            html += f"""
                <div style="position: absolute;
                            top: {position_y}cm;
                            left: {position_x}cm;
                            font-size: {font_size}pt;
                            font-family: {font_family};
                            color: {font_color};
                            {('font-weight: bold;' if is_bold else '')}
                            {('font-style: italic;' if is_italic else '')}
                            z-index: 1;">
                    {field_value}
                </div>
                """

    # Close the HTML
    html += """
        </body>
        </html>
        """

    return html

def export_registrations_csv(request):
    if not request.user.is_admin and not request.user.is_event_manager:
        return HttpResponseForbidden("You don't have permission to export registrations.")

    registrations = Registration.objects.select_related('user', 'event', 'ticket_type').all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="registrations.csv"'
    writer = csv.writer(response)

    # Base columns (non-registration data fields)
    base_columns = [
        "Username", "First Name", "Last Name", "Email", "Title",
        "Phone", "Registration Date", "Event Name", "Ticket Type Name"
    ]
    base_columns_set = set(base_columns)  # For duplicate checking

    # Get unique registration data fields that don't match base columns
    registration_data_fields = set()
    for registration in registrations:
        registration_data = registration.get_registration_data()
        if isinstance(registration_data, str):
            registration_data = json.loads(registration_data)
        # Filter out fields that exist in base columns
        for field in registration_data.keys():
            if field not in base_columns_set:
                registration_data_fields.add(field)

    # Create header row
    header_row = base_columns + sorted(list(registration_data_fields))
    writer.writerow(header_row)

    # Write data rows
    for registration in registrations:
        registration_data = registration.get_registration_data()
        if isinstance(registration_data, str):
            registration_data = json.loads(registration_data)

        # Base data
        row_data = [
            registration.user.username,
            registration.user.first_name,
            registration.user.last_name,
            registration.user.email,
            registration.user.title,
            registration.user.phone_number or "N/A",
            registration.registered_at.strftime("%Y-%m-%d %H:%M:%S"),
            registration.event.name,
            registration.ticket_type.name if registration.ticket_type else "N/A",
        ]

        # Add registration data (only fields not in base columns)
        for field in sorted(list(registration_data_fields)):
            row_data.append(registration_data.get(field, ""))

        writer.writerow(row_data)

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
    Handles the event registration process and prints badge upon successful registration.
    """
    # Fetch all active events
    events = Event.objects.filter(is_active=True).prefetch_related("ticket_types", "custom_fields")

    if request.method == "POST":
        # Retrieve event_id from form POST data
        event_id = request.POST.get("event_id")

        if not event_id:
            messages.error(request, "Event ID is missing.")
            return redirect("registration:create_registration")

        # Validate event existence
        try:
            selected_event = Event.objects.get(id=event_id, is_active=True)
        except Event.DoesNotExist:
            messages.error(request, "The selected event does not exist.")
            return redirect("registration:create_registration")

        # Validate custom fields
        registration_data = {}
        fields = selected_event.custom_fields.all()
        for field in fields:
            field_value = request.POST.get(field.field_name, "").strip()
            if field.is_required and not field_value:
                messages.error(request, f"'{field.field_name}' is required.")
                return redirect("registration:create_registration")
            registration_data[field.field_name] = field_value

        # Validate ticket selection
        ticket_id = request.POST.get("ticket_type")
        if not ticket_id:
            messages.error(request, "Please select a ticket.")
            return redirect("registration:create_registration")

        try:
            ticket = Ticket.objects.get(id=ticket_id, event=selected_event)
        except Ticket.DoesNotExist:
            messages.error(request, "Invalid ticket selection.")
            return redirect("registration:create_registration")

        CustomUser = get_user_model()

        # User data
        user_data = registration_data
        random_password = generate_secure_password()

        # Define the fields that need to be checked
        fields_to_check = ["Email", "First Name", "Last Name", "Phone Number", "Title", "Country"]

        # Ensure no field is null by setting it to an empty string if it is
        for field in fields_to_check:
            user_data[field] = user_data.get(field, "")

        # Create the user with the sanitized data
        new_user = CustomUser.objects.create_user(
            username=random_password,
            email=user_data["Email"],
            first_name=user_data['First Name'],
            last_name=user_data["Last Name"],
            phone_number=user_data["Phone Number"],
            title=user_data["Title"],
            role="VISITOR",
            country=user_data["Country"],
            password=random_password,
        )

        # Save the user
        new_user.save()

        # Create the registration
        registration = Registration.objects.create(
            event=selected_event,
            user=new_user,
            ticket_type=ticket,
            registration_data=json.dumps(registration_data),
        )

        messages.success(request, f"Successfully registered for {selected_event.name}!")

        # Instead of redirecting, render the badge page directly
        badge_template = BadgeTemplate.objects.filter(ticket__event=registration.event).first()

        if badge_template:
            badge_contents = BadgeContent.objects.filter(template=badge_template)
            badge_data = {}

            for content in badge_contents:
                if content.field_name == 'registration__qr_code':
                    badge_data[content.field_name] = content.get_qr_code_image_path(registration)
                else:
                    badge_data[content.field_name] = content.get_field_value(registration)

            # Render the badge template with auto-print script
            return render(request, "registration/registration_badge_autoprint.html", {
                "registration": registration,
                "badge_template": badge_template,
                "badge_data": badge_data,
                "badge_contents": badge_contents,
                "auto_print": True  # Flag to trigger automatic printing
            })

        else:
            messages.error(request, f"to badge template  for {selected_event.name}!")

        # If no badge template exists, redirect to registration page
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


from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Max


@login_required
def manage_registration_fields(request, event_id):
    if not is_admin(request.user) and not is_event_manager(request.user):
        return HttpResponseForbidden("You don't have permission to manage registration fields.")

    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        if 'reorder' in request.POST:
            field_order = request.POST.getlist('field_order[]')
            for index, field_id in enumerate(field_order):
                RegistrationField.objects.filter(id=field_id).update(order=index)
            return JsonResponse({'status': 'success'})

        field_id = request.POST.get('field_id')
        if field_id:
            field = get_object_or_404(RegistrationField, id=field_id, event=event)
            form = RegistrationFieldForm(request.POST, instance=field)
        else:
            form = RegistrationFieldForm(request.POST)

        if form.is_valid():
            field = form.save(commit=False)
            field.event = event

            if field.field_type == 'dropdown':
                options = form.cleaned_data.get('options', '')
                options_list = [opt.strip() for opt in options.split(',') if opt.strip()]
                field.options = ','.join(options_list) if options_list else None

            if not field_id:
                last_order = RegistrationField.objects.filter(event=event).aggregate(Max('order'))['order__max'] or 0
                field.order = last_order + 1

            field.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                fields = RegistrationField.objects.filter(event=event).order_by('order')
                html = render_to_string('registration/fields_table.html',
                                        {'fields': fields, 'event': event},
                                        request=request)
                return JsonResponse({
                    'status': 'success',
                    'html': html
                })
            return redirect('registration:admin_manage_registration_fields', event_id=event.id)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            })

    form = RegistrationFieldForm()
    fields = RegistrationField.objects.filter(event=event).order_by('order')
    return render(request, 'registration/admin_manage_registration_fields.html', {
        'form': form,
        'fields': fields,
        'event': event
    })


@login_required
def get_field_form(request, event_id, field_id):
    if not is_admin(request.user) and not is_event_manager(request.user):
        return JsonResponse({
            'status': 'error',
            'message': 'Permission denied'
        }, status=403)

    try:
        event = get_object_or_404(Event, id=event_id)
        field = get_object_or_404(RegistrationField, id=field_id, event=event)

        form = RegistrationFieldForm(instance=field)

        form_html = render_to_string('registration/field_form.html', {
            'form': form,
            'field': field,
            'event': event
        }, request=request)

        return JsonResponse({
            'status': 'success',
            'form_html': form_html
        })
    except Exception as e:
        print(f"Error in get_field_form: {str(e)}")  # For server-side debugging
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

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
    try:
        qr_code = QRCode.objects.get(registration=registration)
    except:
        qr_code=None
        pass

    # Fetch badge template and badge data
    badge_template = BadgeTemplate.objects.filter(ticket__event=registration.event).first()
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


    badge_template = BadgeTemplate.objects.filter(ticket__event=registration.event).first()

    # If no template exists, return a better formatted error message
    if not badge_template:
        event_name = registration.event.name
        html_message = f"""
        <html>
        <head>
            <title>Badge Template Not Found</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error-container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                h2 {{ color: #d9534f; }}
                .button {{ display: inline-block; padding: 10px 15px; background: #337ab7; color: white; 
                         text-decoration: none; border-radius: 4px; margin-top: 15px; }}
                .button:hover {{ background: #23527c; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h2>Badge Template Not Found</h2>
                <p>No badge template has been created for event: <strong>{event_name}</strong></p>
                <p>Please contact the event organizer to have a badge template created.</p>
                <a class="button" href="javascript:history.back()">Go Back</a>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_message, status=404)
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




