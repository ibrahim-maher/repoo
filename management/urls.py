# management/urls.py
from django.urls import path
from .views import dashboard_views, export_views

app_name = 'management'


urlpatterns = [
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    path('export/', export_views.export_csv, name='export'),
]