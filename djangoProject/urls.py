from django.urls import path, include
from .views import home,admins
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/register_ticket/', views.register_event, name='register_ticket'),


    path('', home, name='home'),  # Home page
    path('admins', admins, name='admins'),  # Home page

    path('users/', include(('users.urls', 'users'), namespace='users')),
    path('events/', include(('events.urls', 'events'), namespace='events')),
    path('registration/', include(('registration.urls', 'registration'), namespace='registration')),
    path('management/', include('management.urls', namespace='management')),
    path('checkin/', include(('checkin.urls', 'checkin'),namespace='checkin')),  # Namespace for the checkin app
    path('badges/', include(('badges.urls', 'badges'))),

]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# Serving media files in production
if settings.DEBUG is False:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
