# management/views/export_views.py
import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required  # Import the login_required decorator

from ..models import DashboardMetric

@login_required
def export_csv(request):
    metrics = DashboardMetric.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="metrics.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Value'])
    for metric in metrics:
        writer.writerow([metric.name, metric.value])

    return response