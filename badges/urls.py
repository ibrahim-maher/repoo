from django.urls import path

from .views import badge_views
from .views.badge_views import create_or_edit_badge_template, preview_badge, save_all_badge_changes

app_name = 'badges'

urlpatterns = [
    path('template/create/', create_or_edit_badge_template, name='create_template'),
    path('template/preview/<int:template_id>/', preview_badge, name='preview_badge'),
    path('edit/<int:template_id>/', badge_views.create_or_edit_badge_template, name='edit_badge_template'),
    path('get-tickets/', badge_views.get_tickets, name='get_tickets'),
    path('badges/save-all/', save_all_badge_changes, name='save_all_badge_changes'),  # Ensure this is present

]
