from django.urls import path
from .views import calendar_views, event_views, filter_views

app_name = 'events'

urlpatterns = [
    # Calendar URL
    path('calendar/', calendar_views.calendar_view, name='calendar'),

    # Event URLs
    path('list/', event_views.event_list_view, name='list'),
    path('detail/<int:event_id>/', event_views.event_detail, name='detail'),
    path('create/', event_views.event_create, name='create'),
    path('update/<int:event_id>/', event_views.event_update, name='update'),
    path('delete/<int:event_id>/', event_views.event_delete, name='delete'),
    path('import_csv/', event_views.import_events_csv, name='import_csv'),
    path('export_csv/', event_views.export_events_csv, name='export_csv'),

    # Venue URLs
    path('venues/', event_views.venue_list, name='venue_list'),
    path('venues/create/', event_views.venue_create, name='venue_create'),
    path('venues/<int:venue_id>/update/', event_views.venue_update, name='venue_update'),
    path('venues/<int:venue_id>/delete/', event_views.venue_delete, name='venue_delete'),
    path('venues/import_csv/', event_views.import_venues_csv, name='import_venues_csv'),
    path('venues/export_csv/', event_views.export_venues_csv, name='export_venues_csv'),

    # Category URLs
    path('categories/', event_views.category_list, name='category_list'),
    path('categories/<int:category_id>/', event_views.category_detail, name='category_detail'),
    path('categories/create/', event_views.category_create, name='category_create'),
    path('categories/<int:category_id>/update/', event_views.category_update, name='category_update'),
    path('categories/<int:category_id>/delete/', event_views.category_delete, name='category_delete'),
    path('categories/import_csv/', event_views.import_categories_csv, name='import_categories_csv'),
    path('categories/export_csv/', event_views.export_categories_csv, name='export_categories_csv'),

    # Recurrence URLs
    path('recurrences/', event_views.recurrence_list, name='recurrence_list'),
    path('recurrences/<int:recurrence_id>/', event_views.recurrence_detail, name='recurrence_detail'),
    path('recurrences/create/', event_views.recurrence_create, name='recurrence_create'),
    path('recurrences/<int:recurrence_id>/update/', event_views.recurrence_update, name='recurrence_update'),
    path('recurrences/<int:recurrence_id>/delete/', event_views.recurrence_delete, name='recurrence_delete'),
    path('recurrences/import_csv/', event_views.import_recurrences_csv, name='import_recurrences_csv'),
    path('recurrences/export_csv/', event_views.export_recurrences_csv, name='export_recurrences_csv'),

    # Filter URL
    path('filter/', filter_views.filter_events, name='filter'),
]
