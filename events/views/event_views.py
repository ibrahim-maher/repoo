import csv
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect

from registration.models import RegistrationField
from ..models import Venue, Category, Recurrence
from ..forms import EventForm, VenueForm, CategoryForm, RecurrenceForm

def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'


def is_event_manager(user):
    return user.is_authenticated and user.role == 'EVENT_MANAGER'


# Event Views

from django.shortcuts import render
from django.urls import reverse
from ..models import Event

@login_required

def event_list_view(request):

    search_query = request.GET.get("search", "")

   
    events = Event.objects.all()


    if search_query:
        events = events.filter(name__icontains=search_query)

    paginator = Paginator(events, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    rows = [
        {
            "cells": [
                event.name,
                event.description[:50] + "..." if event.description else "",
                event.start_date.strftime("%Y-%m-%d %H:%M"),
                event.end_date.strftime("%Y-%m-%d %H:%M"),
                event.venue.name if event.venue else "N/A",
                event.category.name if event.category else "N/A",
                event.is_active,
            ],
            "actions": [
                {
                    "url": reverse("events:detail", args=[event.id]),
                    "class": "info",
                    "icon": "la la-eye",
                    "label": "View",
                },
                {
                    "url": reverse("events:update", args=[event.id]),
                    "class": "warning",
                    "icon": "la la-edit",
                    "label": "Edit",
                },
                {
                    "url": reverse("events:delete", args=[event.id]),
                    "class": "danger",
                    "icon": "la la-trash",
                    "label": "Delete",
                },
            ],
        }
        for event in page_obj
    ]

    context = {
        "heading": "Events",
        "table_heading": "All Events",
        "columns": ["Number","Name", "Description", "Start Date", "End Date", "Venue", "Category","Active"],
        "rows": rows,
        "show_create_button": False  if is_admin else True,
        "create_action": reverse("events:create"),
        "create_button_label": "Create Event",
        "search_action": reverse("events:list"),
        "search_placeholder": "Search Events...",
        "search_query": search_query,
        "show_export_button": True,
        "export_action": reverse("events:export_csv"),
        "export_button_label": "Export CSV",
        "show_import_button": False,
        "import_action": reverse("events:import_csv"),
        "import_button_label": "Import CSV",
        "paginator": paginator,
        "page_obj": page_obj,
    }

    return render(request, "events/event_list.html", context)
def export_events_csv(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to export events.")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="events.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Description', 'Start Date', 'End Date', 'Venue', 'Category'])

    events = Event.objects.all()
    for event in events:
        writer.writerow([event.name, event.description, event.start_date, event.end_date, event.venue.name, event.category.name])

    return response

def import_events_csv(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to import events.")

    if request.method == 'POST' and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            return render(request, 'events/event_list.html', {'error_message': 'Please upload a valid CSV file.', 'events': Event.objects.all()})

        file_data = csv_file.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(file_data)
        next(csv_reader)

        for row in csv_reader:
            try:
                venue, _ = Venue.objects.get_or_create(name=row[4])
                category, _ = Category.objects.get_or_create(name=row[5])
                Event.objects.update_or_create(
                    name=row[0],
                    defaults={
                        'description': row[1],
                        'start_date': row[2],
                        'end_date': row[3],
                        'venue': venue,
                        'category': category,
                    }
                )
            except Exception as e:
                return render(request, 'events/event_list.html', {
                    'error_message': f'Error processing row: {row}. {str(e)}',
                    'events': Event.objects.all(),
                })

        return redirect('events:event_list')
    return redirect('events:event_list')


@receiver(post_save, sender=Event)
def create_default_registration_fields(sender, instance, created, **kwargs):
    """
    Automatically creates default registration fields for a new event.
    """
    if created:  # Only when an event is newly created
        for field in RegistrationField.DEFAULT_FIELDS:
            RegistrationField.objects.create(
                event=instance,
                field_name=field['field_name'],
                field_type=field['field_type'],
                is_required=field['is_required'],
            )
def export_venues_csv(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to export venues.")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="venues.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Address', 'Capacity'])

    venues = Venue.objects.all()
    for venue in venues:
        writer.writerow([venue.name, venue.address, venue.capacity])

    return response

def import_venues_csv(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to import venues.")

    if request.method == 'POST' and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            return render(request, 'events/venue_list.html', {'error_message': 'Please upload a valid CSV file.', 'venues': Venue.objects.all()})

        file_data = csv_file.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(file_data)
        next(csv_reader)  # Skip the header row

        for row in csv_reader:
            try:
                Venue.objects.update_or_create(
                    name=row[0],
                    defaults={
                        'address': row[1],
                        'capacity': row[2]
                    }
                )
            except Exception as e:
                return render(request, 'events/venue_list.html', {
                    'error_message': f'Error processing row: {row}. {str(e)}',
                    'venues': Venue.objects.all(),
                })

        return redirect('events:venue_list')
    return redirect('events:venue_list')


def export_categories_csv(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to export categories.")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="categories.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name'])

    categories = Category.objects.all()
    for category in categories:
        writer.writerow([category.name])

    return response

def import_categories_csv(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to import categories.")

    if request.method == 'POST' and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            return render(request, 'events/category_list.html', {'error_message': 'Please upload a valid CSV file.', 'categories': Category.objects.all()})

        file_data = csv_file.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(file_data)
        next(csv_reader)  # Skip the header row

        for row in csv_reader:
            try:
                Category.objects.update_or_create(name=row[0])
            except Exception as e:
                return render(request, 'events/category_list.html', {
                    'error_message': f'Error processing row: {row}. {str(e)}',
                    'categories': Category.objects.all(),
                })

        return redirect('events:category_list')
    return redirect('events:category_list')
def export_recurrences_csv(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to export recurrences.")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="recurrences.csv"'

    writer = csv.writer(response)
    writer.writerow(['Event', 'Recurrence Type', 'Interval', 'End Date'])

    recurrences = Recurrence.objects.select_related('event').all()
    for recurrence in recurrences:
        writer.writerow([
            recurrence.event.name,
            recurrence.recurrence_type,
            recurrence.interval,
            recurrence.end_date
        ])

    return response

def import_recurrences_csv(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to import recurrences.")

    if request.method == 'POST' and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            return render(request, 'events/recurrence_list.html', {'error_message': 'Please upload a valid CSV file.', 'recurrences': Recurrence.objects.all()})

        file_data = csv_file.read().decode('utf-8').splitlines()
        csv_reader = csv.reader(file_data)
        next(csv_reader)  # Skip the header row

        for row in csv_reader:
            try:
                event = Event.objects.get(name=row[0])
                Recurrence.objects.update_or_create(
                    event=event,
                    recurrence_type=row[1],
                    defaults={
                        'interval': row[2],
                        'end_date': row[3]
                    }
                )
            except Exception as e:
                return render(request, 'events/recurrence_list.html', {
                    'error_message': f'Error processing row: {row}. {str(e)}',
                    'recurrences': Recurrence.objects.all(),
                })

        return redirect('events:recurrence_list')
    return redirect('events:recurrence_list')

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if is_event_manager(request.user) and event.created_by != request.user:
        return HttpResponseForbidden("You don't have permission to view this event.")
    return render(request, 'events/event_detail.html', {'event': event})


def event_create(request):
    if not (is_event_manager(request.user) or is_admin(request.user)):
        return HttpResponseForbidden("You don't have permission to create events.")

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            if is_event_manager(request.user):
                event.created_by = request.user
            event.save()
            return redirect('events:list')
    else:
        form = EventForm()
    return render(request, 'events/event_form.html', {'form': form})


def event_update(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Check if the user is allowed to update the event
    if is_event_manager(request.user) and event.created_by != request.user:
        return HttpResponseForbidden("You don't have permission to edit this event.")

    if request.method == 'POST':
        # Crucially, pass both request.POST and request.FILES
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            # If a new logo is uploaded, replace the existing one
            if 'logo' in request.FILES:
                # Delete the old logo file if it exists
                if event.logo:
                    event.logo.delete()
                event.logo = request.FILES['logo']

            # Save the event
            form.save()

            # If logo was cleared, ensure it's set to None
            if form.cleaned_data.get('logo') is False:
                event.logo = None
                event.save()

            return redirect('events:detail', event_id=event.id)
        else:
            # Print form errors for debugging
            print(form.errors)
    else:
        form = EventForm(instance=event)

    return render(request, 'events/event_form.html', {'form': form})

def event_delete(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if is_event_manager(request.user) and event.created_by != request.user:
        return HttpResponseForbidden("You don't have permission to delete this event.")

    if request.method == 'POST':
        event.delete()
        return redirect('events:list')
    return render(request, 'events/event_confirm_delete.html', {'event': event})


@login_required

def venue_list(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to view venues.")

    search_query = request.GET.get("search", "")
    venues = Venue.objects.all()

    # Filter venues by search query
    if search_query:
        venues = venues.filter(name__icontains=search_query)

    # Create paginator with 20 venues per page
    paginator = Paginator(venues, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Create rows for current page only
    rows = [
        {
            "cells": [
                venue.name,
                venue.address,
                venue.capacity,
            ],
            "actions": [
                {
                    "url": reverse("events:venue_update", args=[venue.id]),
                    "class": "warning",
                    "icon": "la la-edit",
                    "label": "Edit",
                },
                {
                    "url": reverse("events:venue_delete", args=[venue.id]),
                    "class": "danger",
                    "icon": "la la-trash",
                    "label": "Delete",
                },
            ],
        }
        for venue in page_obj
    ]

    context = {
        "heading": "Venues",
        "table_heading": "Venue List",
        "columns": ["Number","Name", "Address", "Capacity"],
        "rows": rows,
        "show_create_button": True,
        "create_action": reverse("events:venue_create"),
        "create_button_label": "Create New Venue",
        "search_action": reverse("events:venue_list"),
        "search_placeholder": "Search Venues...",
        "search_query": search_query,
        "show_export_button": True,  # Show export button
        "export_action": reverse("events:export_venues_csv"),  # Link to export CSV
        "export_button_label": "Export CSV",
        "show_import_button": True,  # Show import button
        "import_action": reverse("events:import_venues_csv"),  # Link to import CSV
        "import_button_label": "Import CSV",
        # Add pagination context
        "paginator": paginator,
        "page_obj": page_obj,
    }

    return render(request, "events/venue_list.html", context)

@login_required
def venue_create(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to create venues.")
    if request.method == 'POST':
        form = VenueForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('events:venue_list')
    else:
        form = VenueForm()
    return render(request, 'events/venue_form.html', {'form': form})


def venue_update(request, venue_id):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to update venues.")
    venue = get_object_or_404(Venue, id=venue_id)
    if request.method == 'POST':
        form = VenueForm(request.POST, instance=venue)
        if form.is_valid():
            form.save()
            return redirect('events:venue_detail', venue_id=venue.id)
    else:
        form = VenueForm(instance=venue)
    return render(request, 'events/venue_form.html', {'form': form})


def venue_delete(request, venue_id):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to delete venues.")
    venue = get_object_or_404(Venue, id=venue_id)
    if request.method == 'POST':
        venue.delete()
        return redirect('events:venue_list')
    return render(request, 'events/venue_confirm_delete.html', {'venue': venue})


# Category Views
@login_required
def category_list(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to view categories.")

    # Apply search if present
    search_query = request.GET.get("search", "")
    categories = Category.objects.all()
    if search_query:
        categories = categories.filter(name__icontains=search_query)

    # Create paginator with 20 categories per page
    paginator = Paginator(categories, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Create rows for current page only
    rows = [
        {
            "cells": [
                category.name,
            ],
            "actions": [

                {
                    "url": reverse("events:category_update", args=[category.id]),
                    "class": "warning",
                    "icon": "la la-edit",
                    "label": "Edit",
                },
                {
                    "url": reverse("events:category_delete", args=[category.id]),
                    "class": "danger",
                    "icon": "la la-trash",
                    "label": "Delete",
                },
            ],
        }
        for category in page_obj
    ]

    context = {
        "heading": "Categories",
        "table_heading": "Category List",
        "columns": ["Number","Name"],
        "rows": rows,
        "show_create_button": True,
        "create_action": reverse("events:category_create"),
        "create_button_label": "Create New Category",
        "search_action": reverse("events:category_list"),
        "search_placeholder": "Search Categories...",
        "search_query": search_query,
        "show_export_button": True,  # Show export button
        "export_action": reverse("events:export_categories_csv"),  # Link to export CSV
        "export_button_label": "Export CSV",
        "show_import_button": True,  # Show import button
        "import_action": reverse("events:import_categories_csv"),  # Link to import CSV
        "import_button_label": "Import CSV",
        # Add pagination context
        "paginator": paginator,
        "page_obj": page_obj,
    }

    return render(request, "events/category_list.html", context)
def category_detail(request, category_id):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to view category details.")
    category = get_object_or_404(Category, id=category_id)
    return render(request, 'events/category_detail.html', {'category': category})

@login_required

def category_create(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to create categories.")
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('events:category_list')
    else:
        form = CategoryForm()
    return render(request, 'events/category_form.html', {'form': form})

@login_required

def category_update(request, category_id):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to update categories.")
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('events:category_detail', category_id=category.id)
    else:
        form = CategoryForm(instance=category)
    return render(request, 'events/category_form.html', {'form': form})


def category_delete(request, category_id):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to delete categories.")
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        return redirect('events:category_list')
    return render(request, 'events/category_confirm_delete.html', {'category': category})


# Recurrence Views
@login_required

def recurrence_list(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to view recurrences.")
    recurrences = Recurrence.objects.all()
    return render(request, 'events/recurrence_list.html', {'recurrences': recurrences})


def recurrence_detail(request, recurrence_id):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to view recurrence details.")
    recurrence = get_object_or_404(Recurrence, id=recurrence_id)
    return render(request, 'events/recurrence_detail.html', {'recurrence': recurrence})


def recurrence_create(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to create recurrences.")
    if request.method == 'POST':
        form = RecurrenceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('events:recurrence_list')
    else:
        form = RecurrenceForm()
    return render(request, 'events/recurrence_form.html', {'form': form})


def recurrence_update(request, recurrence_id):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to update recurrences.")
    recurrence = get_object_or_404(Recurrence, id=recurrence_id)
    if request.method == 'POST':
        form = RecurrenceForm(request.POST, instance=recurrence)
        if form.is_valid():
            form.save()
            return redirect('events:recurrence_detail', recurrence_id=recurrence.id)
    else:
        form = RecurrenceForm(instance=recurrence)
    return render(request, 'events/recurrence_form.html', {'form': form})


def recurrence_delete(request, recurrence_id):
    if not is_admin(request.user):
        return HttpResponseForbidden("You don't have permission to delete recurrences.")
    recurrence = get_object_or_404(Recurrence, id=recurrence_id)
    if request.method == 'POST':
        recurrence.delete()
        return redirect('events:recurrence_list')
    return render(request, 'events/recurrence_confirm_delete.html', {'recurrence': recurrence})
