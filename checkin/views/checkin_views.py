from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseServerError
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.csrf import ensure_csrf_cookie
import json
import traceback

from checkin.forms import ManualCheckInForm
from registration.models import Registration
from checkin.models import VisitorLog


@login_required
@ensure_csrf_cookie
def checkin_page(request):
    """Render the check-in page with QR scanner"""
    return render(request, 'checkin/checkin.html')


@login_required
@ensure_csrf_cookie
def checkout_page(request):
    """Render the check-out page with QR scanner"""
    return render(request, 'checkin/checkout.html')


@login_required
@require_http_methods(["POST"])
def process_qr_scan(request):
    try:
        data = json.loads(request.body)
        registration_id = data.get('registration_id')

        print(f"Processing QR scan for registration ID: {registration_id}")

        with transaction.atomic():
            try:
                registration = Registration.objects.get(id=registration_id)
            except Registration.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Registration ID {registration_id} not found'
                }, status=404)

            # Check if event is active
            if not registration.event.is_active:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Event is not active'
                }, status=400)

            # Determine action based on last log
            last_log = VisitorLog.objects.filter(registration=registration).order_by('-timestamp').first()
            action = 'checkout' if last_log and last_log.action == 'checkin' else 'checkin'

            # Create the log
            log = VisitorLog.objects.create(
                registration=registration,
                action=action,
                created_by=request.user
            )

            print(f"Created log: {log}, action: {action}")

            return JsonResponse({
                'status': 'success',
                'action': action,
                'timestamp': log.timestamp.isoformat(),
                'user': registration.user.email
            })

    except Exception as e:
        print(f"Error in process_qr_scan: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def manual_checkin(request):
    try:
        # Debug information
        print("Manual check-in POST data:", request.POST)

        form = ManualCheckInForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    registration_id = form.cleaned_data['registration_id']

                    # Get the registration
                    try:
                        registration = Registration.objects.get(id=registration_id)
                    except Registration.DoesNotExist:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Registration ID {registration_id} not found'
                        }, status=404)

                    # Create log
                    log = VisitorLog.objects.create(
                        registration=registration,
                        action='checkin',
                        admin_note=form.cleaned_data.get('admin_note', ''),
                        created_by=request.user
                    )

                    print(f"Manual check-in successful for registration {registration_id}")

                    return JsonResponse({
                        'status': 'success',
                        'message': f'Successfully checked in {registration.user.email}'
                    })
            except Exception as e:
                error_msg = f"Error processing check-in: {str(e)}"
                print(error_msg)
                print(traceback.format_exc())
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
        else:
            # Return detailed form errors
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")

            print(f"Form validation failed: {error_messages}")

            return JsonResponse({
                'status': 'error',
                'message': 'Invalid form data',
                'errors': error_messages
            }, status=400)
    except Exception as e:
        print(f"Unexpected error in manual_checkin: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def manual_checkout(request):
    try:
        # Debug information
        print("Manual check-out POST data:", request.POST)

        form = ManualCheckInForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    registration_id = form.cleaned_data['registration_id']

                    # Get the registration
                    try:
                        registration = Registration.objects.get(id=registration_id)
                    except Registration.DoesNotExist:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Registration ID {registration_id} not found'
                        }, status=404)

                    # Create log
                    log = VisitorLog.objects.create(
                        registration=registration,
                        action='checkout',
                        admin_note=form.cleaned_data.get('admin_note', ''),
                        created_by=request.user
                    )

                    print(f"Manual check-out successful for registration {registration_id}")

                    return JsonResponse({
                        'status': 'success',
                        'message': f'Successfully checked out {registration.user.email}'
                    })
            except Exception as e:
                error_msg = f"Error processing check-out: {str(e)}"
                print(error_msg)
                print(traceback.format_exc())
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
        else:
            # Return detailed form errors
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")

            print(f"Form validation failed: {error_messages}")

            return JsonResponse({
                'status': 'error',
                'message': 'Invalid form data',
                'errors': error_messages
            }, status=400)
    except Exception as e:
        print(f"Unexpected error in manual_checkout: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=500)


@login_required
def badge_screen(request):
    """Render the screen for scanning QR code or manually entering Registration ID for badge generation."""
    return render(request, 'checkin/registration_badge.html')



@login_required
@ensure_csrf_cookie
def scan_for_print(request):
    """Render the scan for print page with QR scanner"""
    return render(request, 'checkin/scan_for_print.html')


@login_required
@require_http_methods(["POST"])
def verify_registration(request):
    """
    Verify if a registration ID exists
    This endpoint is used by the scan for print page to check if a registration exists
    before redirecting to the details page
    """
    try:
        data = json.loads(request.body)
        registration_id = data.get('registration_id')

        if not registration_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Registration ID is required'
            }, status=400)

        try:
            # Check if registration exists
            registration = Registration.objects.get(id=registration_id)
            return JsonResponse({
                'status': 'success',
                'message': 'Registration found'
            })
        except Registration.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': f'Registration ID {registration_id} not found'
            }, status=404)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }, status=500)
