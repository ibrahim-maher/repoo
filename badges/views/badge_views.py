from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.urls import reverse
import logging

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from registration.models import Registration
from ..models import BadgeTemplate, BadgeContent
from ..forms import BadgeTemplateForm, BadgeContentFormSet
from events.models import Event

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

    selected_event = None
    existing_template = None

    if request.method == 'GET':
        event_id = request.GET.get('event')
        if event_id:
            selected_event = get_object_or_404(Event, id=event_id)
            existing_template = BadgeTemplate.objects.filter(event=selected_event).first()

            # If it's an AJAX request, return only the form HTML
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                template_form = BadgeTemplateForm(instance=existing_template)
                formset = BadgeContentFormSet(
                    queryset=BadgeContent.objects.filter(
                        template=existing_template) if existing_template else BadgeContent.objects.none()
                )
                context = {
                    'template_form': template_form,
                    'formset': formset,
                    'selected_event': selected_event,
                }
                return render(request, 'badges/partial_template_form.html', context)

    if request.method == 'POST':
        event_id = request.POST.get('event')
        if event_id:
            selected_event = get_object_or_404(Event, id=event_id)
            existing_template = BadgeTemplate.objects.filter(event=selected_event).first()

        template_form = BadgeTemplateForm(
            request.POST,
            request.FILES,
            instance=existing_template
        )

        formset = BadgeContentFormSet(
            request.POST,
            queryset=BadgeContent.objects.filter(
                template=existing_template) if existing_template else BadgeContent.objects.none()
        )

        if template_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Save the template
                    badge_template = template_form.save(commit=False)
                    if not selected_event:
                        raise ValidationError("You must select an event.")
                    badge_template.event = selected_event
                    badge_template.created_by = request.user
                    badge_template.save()

                    # Handle the formset
                    instances = formset.save(commit=False)

                    # Delete the removed forms
                    for obj in formset.deleted_objects:
                        obj.delete()

                    # Save new and updated instances
                    for instance in instances:
                        instance.template = badge_template
                        instance.save()

                    messages.success(request, "Badge template saved successfully!")
                    return redirect('badges:preview_badge', template_id=badge_template.id)

            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Error saving badge template: {str(e)}")
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        template_form = BadgeTemplateForm(instance=existing_template)
        formset = BadgeContentFormSet(
            queryset=BadgeContent.objects.filter(
                template=existing_template) if existing_template else BadgeContent.objects.none()
        )

    context = {
        'template_form': template_form,
        'formset': formset,
        'events': events,
        'selected_event': selected_event,
        'existing_template': existing_template,
    }

    return render(request, 'badges/create_template.html', context)

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
    Update badge content field via AJAX
    """
    try:
        content = BadgeContent.objects.get(id=content_id)

        # Update positioning
        content.position_x = float(request.POST.get('position_x', content.position_x))
        content.position_y = float(request.POST.get('position_y', content.position_y))

        # Update styling
        content.font_size = int(request.POST.get('font_size', content.font_size))
        content.font_color = request.POST.get('font_color', content.font_color)
        content.font_family = request.POST.get('font_family', content.font_family)
        content.is_bold = request.POST.get('is_bold', 'false').lower() == 'true'
        content.is_italic = request.POST.get('is_italic', 'false').lower() == 'true'

        content.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Badge content updated successfully'
        })
    except BadgeContent.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Badge content not found'
        }, status=404)


def preview_badge(request, template_id):
    badge_template = get_object_or_404(
        BadgeTemplate.objects.prefetch_related('contents'),
        id=template_id
    )

    return render(request, 'badges/preview_badge.html', {
        'badge_template': badge_template,
        'contents': badge_template.contents.all(),
    })


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
    Update badge content field via AJAX
    """
    try:
        content = BadgeContent.objects.get(id=content_id)

        # Update positioning
        content.position_x = float(request.POST.get('position_x', content.position_x))
        content.position_y = float(request.POST.get('position_y', content.position_y))

        # Update styling
        content.font_size = int(request.POST.get('font_size', content.font_size))
        content.font_color = request.POST.get('font_color', content.font_color)
        content.font_family = request.POST.get('font_family', content.font_family)
        content.is_bold = request.POST.get('is_bold', 'false').lower() == 'true'
        content.is_italic = request.POST.get('is_italic', 'false').lower() == 'true'

        content.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Badge content updated successfully'
        })
    except BadgeContent.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Badge content not found'
        }, status=404)
