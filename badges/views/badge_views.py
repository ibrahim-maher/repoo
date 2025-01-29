from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.urls import reverse
import logging
import json

from registration.models import Registration, Ticket

logger = logging.getLogger(__name__)

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from registration.models import Registration
from ..models import BadgeTemplate, BadgeContent
from ..forms import BadgeTemplateForm, BadgeContentFormSet
from events.models import Event

logger = logging.getLogger(__name__)

import logging

logger = logging.getLogger(__name__)


def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'


def is_event_manager(user):
    return user.is_authenticated and user.role == 'EVENT_MANAGER'


@login_required
def create_or_edit_badge_template(request):
    events = Event.objects.all().order_by('-start_date')
    template_form = None
    formset = None
    ticket = None

    ticket_id = request.GET.get('ticket') or request.POST.get('ticket')

    if ticket_id:
        ticket = get_object_or_404(Ticket, id=ticket_id)
        existing_template = BadgeTemplate.objects.filter(ticket=ticket).first()

        if request.method == 'POST':
            # Handle POST request
            template_form = BadgeTemplateForm(
                request.POST,
                request.FILES,
                instance=existing_template if existing_template else None
            )
            formset = BadgeContentFormSet(
                request.POST,
                queryset=BadgeContent.objects.filter(
                    template=existing_template) if existing_template else BadgeContent.objects.none()
            )

            if template_form.is_valid() and formset.is_valid():
                with transaction.atomic():
                    badge_template = template_form.save(commit=False)
                    badge_template.ticket = ticket
                    badge_template.created_by = request.user
                    badge_template.save()

                    # Delete existing content if updating
                    if existing_template:
                        BadgeContent.objects.filter(template=existing_template).delete()

                    # Save formset content
                    badge_contents = formset.save(commit=False)
                    for badge_content in badge_contents:
                        badge_content.template = badge_template
                        badge_content.save()

                    formset.save_m2m()

                return redirect('badges:preview_badge', template_id=badge_template.id)
        else:
            # Handle GET request
            if existing_template:
                # Load existing template data
                template_form = BadgeTemplateForm(instance=existing_template)
                formset = BadgeContentFormSet(
                    queryset=BadgeContent.objects.filter(template=existing_template)
                )
            else:
                # Initialize new template form for the ticket
                template_form = BadgeTemplateForm(initial={'ticket': ticket})
                formset = BadgeContentFormSet(queryset=BadgeContent.objects.none())

    # If no ticket_id or form initialization needed
    if template_form is None:
        template_form = BadgeTemplateForm()
        formset = BadgeContentFormSet(queryset=BadgeContent.objects.none())

    context = {
        'template_form': template_form,
        'formset': formset,
        'events': events,
        'selected_event': ticket.event if ticket else None,
    }

    return render(request, 'badges/create_template.html', context)





@login_required
def get_tickets(request):
    """AJAX view to get tickets for selected event"""
    event_id = request.GET.get('event_id')
    if event_id:
        tickets = Ticket.objects.filter(event_id=event_id).values('id', 'name')
        return JsonResponse(list(tickets), safe=False)
    return JsonResponse([], safe=False)


def preview_badge(request, template_id):
    """
    Render badge preview with interactive field positioning and styling.
    """
    badge_template = get_object_or_404(
        BadgeTemplate.objects.prefetch_related('contents'),
        id=template_id
    )

    return render(request, 'badges/preview_badge.html', {
        'badge_template': badge_template,
        'contents': badge_template.contents.all(),
    })


@csrf_exempt
@require_POST
def update_badge_content(request, content_id):
    """
    Update badge content field via AJAX.
    """
    try:
        content = BadgeContent.objects.get(id=content_id)

        # Update positioning and styling based on the POST data
        content.position_x = float(request.POST.get('position_x', content.position_x))
        content.position_y = float(request.POST.get('position_y', content.position_y))
        content.font_size = int(request.POST.get('font_size', content.font_size))
        content.font_color = request.POST.get('font_color', content.font_color)
        content.font_family = request.POST.get('font_family', content.font_family)
        content.is_bold = request.POST.get('is_bold', 'false').lower() == 'true'
        content.is_italic = request.POST.get('is_italic', 'false').lower() == 'true'

        content.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Badge content updated successfully!'
        })
    except BadgeContent.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Badge content not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=500)


def save_all_badge_changes(request):
    try:
        data = json.loads(request.body)
        updates = data.get('updates', [])

        for update in updates:
            content = BadgeContent.objects.get(id=update['content_id'])
            content.position_x = update['position_x']
            content.position_y = update['position_y']
            content.font_size = update['font_size']
            content.font_color = update['font_color']
            content.font_family = update['font_family']
            content.is_bold = update['is_bold']
            content.is_italic = update['is_italic']
            content.save()

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
