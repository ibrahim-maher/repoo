from django.contrib.auth import get_user_model
from django.db.models import Count, F
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from checkin.models import VisitorLog
from events.models import Event  # Import Event model
from django.contrib.auth.models import User  # Import User model for "Created By"

from users.models import CustomUser


@login_required
def visitor_logs(request):
    """View for displaying visitor logs with filtering"""
    logs = VisitorLog.objects.select_related('registration__user', 'registration__event', 'created_by')

    # Fetch all events for the dropdown
    events = Event.objects.all()
    CustomUser = get_user_model()

    # Fetch all users for the "Created By" dropdown
    created_by_users = CustomUser.objects.filter(created_logs__isnull=False).distinct()

    # Apply filters
    event_id = request.GET.get('event')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    action = request.GET.get('action')
    created_by_id = request.GET.get('created_by')  # Get the created_by filter value

    if event_id:
        logs = logs.filter(registration__event_id=event_id)
    if date_from:
        logs = logs.filter(timestamp__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__lte=date_to)
    if action:
        logs = logs.filter(action=action)
    if created_by_id:
        logs = logs.filter(created_by_id=created_by_id)  # Filter by created_by

    # Paginate logs
    paginator = Paginator(logs, 50)
    page = request.GET.get('page', 1)
    logs_page = paginator.get_page(page)

    # Calculate statistics
    stats = {
        'total_checkins': logs.filter(action='checkin').count(),
        'total_checkouts': logs.filter(action='checkout').count(),
    }

    # Chart data: Hourly distribution
    hourly_distribution = (
        logs.annotate(hour=F('timestamp__hour'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )
    hourly_labels = [f"{hour['hour']:02d}:00" for hour in hourly_distribution]
    hourly_data = [hour['count'] for hour in hourly_distribution]

    return render(request, 'checkin/visitor_log.html', {
        'logs': logs_page,
        'stats': stats,
        'events': events,
        'created_by_users': created_by_users,  # Pass created_by options to the template
        'hourly_labels': hourly_labels,
        'hourly_data': hourly_data,
    })
