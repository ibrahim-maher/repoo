from django.urls import path
from checkin.views import checkin_views, log_views

app_name = 'checkin'  # Add namespace for the app

urlpatterns = [
    path('', checkin_views.checkin_page, name='checkin'),
    path('checkout', checkin_views.checkout_page, name='checkout'),  # Check-in page
    # Check-in page
    path('api/scan/', checkin_views.process_qr_scan, name='process_qr_scan'),  # API for QR scanning
    path('api/manual-checkin/', checkin_views.manual_checkin, name='manual_checkin'),  # API for manual check-in
    path('api/manual-checkout/', checkin_views.manual_checkout, name='manual_checkout'),  # API for manual check-in

    path('logs/', log_views.visitor_logs, name='logs'),  # Visitor logs
    # path('logs/', log_views.visitor_logs, name='logs'),  # Visitor logs
    # path('logs/', log_views.visitor_logs, name='logs'),  # Visitor logs


]
