# management/views/dashboard_views.py
import datetime
from time import timezone

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from registration.models import Registration, Ticket
from users.models import CustomUser, RoleChoices
from ..models import DashboardMetric
from events.models import Event, Venue, Category, Recurrence

from django.shortcuts import render
from events.models import Event, Venue, Category

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from registration.models import Registration, Ticket
from events.models import Event, Venue, Category
from users.models import CustomUser, RoleChoices
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta

@login_required

def dashboard_view(request):
    search_query = request.GET.get('search_query', '').strip()

    # Summary metrics
    total_events = Event.objects.count()
    venues_count = Venue.objects.count()
    categories_count = Category.objects.count()
    registrations_count = Registration.objects.count()
    tickets_count = Ticket.objects.count()
    event_managers_count = CustomUser.objects.filter(role=RoleChoices.EVENT_MANAGER).count()
    ushers_count = CustomUser.objects.filter(role=RoleChoices.USHER).count()
    visitors_count = CustomUser.objects.filter(role=RoleChoices.VISITOR).count()

    # Filtered registrations
    registrations = Registration.objects.all()
    if search_query:
        registrations = registrations.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(event__name__icontains=search_query)
        )

    registrations = registrations.order_by('-registered_at')[:5]

    # Other analytics (unchanged)
    six_months_ago = datetime.now() - timedelta(days=180)
    registrations_by_month = (
        Registration.objects.filter(registered_at__gte=six_months_ago)
        .annotate(month=Count('registered_at__month'))
        .values('registered_at__month')
        .annotate(count=Count('id'))
        .order_by('registered_at__month')
    )
    registration_data = {str(month['registered_at__month']): month['count'] for month in registrations_by_month}

    category_popularity = (
        Registration.objects.values('event__category__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    category_labels = [cat['event__category__name'] for cat in category_popularity]
    category_data = [cat['count'] for cat in category_popularity]

    registrations_per_event = (
        Event.objects.annotate(registration_count=Count('registrations'))
        .values('name', 'registration_count')
        .order_by('-registration_count')
    )

    context = {
        'total_events': total_events,
        'venues_count': venues_count,
        'categories_count': categories_count,
        'registrations_count': registrations_count,
        'tickets_count': tickets_count,
        'event_managers_count': event_managers_count,
        'ushers_count': ushers_count,
        'visitors_count': visitors_count,
        'registration_labels': list(registration_data.keys()),
        'registration_counts': list(registration_data.values()),
        'category_labels': category_labels,
        'category_data': category_data,
        'recent_registrations': registrations,
        'registrations_per_event': registrations_per_event,
        'search_query': search_query,
    }

    return render(request, 'management/dashboard.html', context)

@login_required
def event_manager_dashboard(request):
    metrics = DashboardMetric.objects.all()
    return render(request, 'management/dashboard.html', {'metrics': metrics, 'role': 'Event Manager'})