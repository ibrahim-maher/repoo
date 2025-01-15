from django.core.serializers import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from checkin.forms import ManualCheckInForm
from checkin.models import VisitorLog
from registration.models import Registration


@login_required
@require_http_methods(["GET"])
def checkin_page(request):
    """Render the check-in page with QR scanner"""
    return render(request, 'checkin/checkin.html')
def checkout_page(request):
    """Render the check-in page with QR scanner"""
    return render(request, 'checkin/checkout.html')

@login_required
@require_http_methods(["POST"])
def process_qr_scan(request):
    try:
        data = json.loads(request.body)
        registration_id = data.get('registration_id')

        with transaction.atomic():
            registration = get_object_or_404(Registration, id=registration_id)

            if not registration.event.is_active:
                return JsonResponse({'status': 'error', 'message': 'Event is not active'}, status=400)

            last_log = VisitorLog.objects.filter(registration=registration).order_by('-timestamp').first()
            action = 'checkout' if last_log and last_log.action == 'checkin' else 'checkin'

            log = VisitorLog.objects.create(
                registration=registration,
                action=action,
                created_by=request.user
            )

            return JsonResponse({
                'status': 'success',
                'action': action,
                'timestamp': log.timestamp.isoformat(),
                'user': registration.user.username
            })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def manual_checkin(request):
    form = ManualCheckInForm(request.POST)
    if form.is_valid():
        try:
            with transaction.atomic():
                registration = get_object_or_404(
                    Registration,
                    id=form.cleaned_data['registration_id']
                )

                log = VisitorLog.objects.create(
                    registration=registration,
                    action=form.cleaned_data['action'],
                    admin_note=form.cleaned_data['admin_note'],
                    created_by=request.user
                )

                return JsonResponse({'status': 'success', 'message': f'Successfully processed {log.action}'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid form data'}, status=400)


@login_required
@require_http_methods(["POST"])
def manual_checkout(request):
    form = ManualCheckInForm(request.POST)
    if form.is_valid():
        try:
            with transaction.atomic():
                registration = get_object_or_404(
                    Registration,
                    id=form.cleaned_data['registration_id']
                )

                log = VisitorLog.objects.create(
                    registration=registration,
                    action=form.cleaned_data['action'],
                    admin_note=form.cleaned_data['admin_note'],
                    created_by=request.user
                )

                return JsonResponse({'status': 'success', 'message': f'Successfully processed {log.action}'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid form data'}, status=400)

@login_required

def badge_screen(request):
    """Render the screen for scanning QR code or manually entering Registration ID for badge generation."""
    return render(request, 'checkin/registration_badge.html')