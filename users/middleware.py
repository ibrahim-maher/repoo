from django.shortcuts import redirect
from django.urls import reverse

class RoleBasedRedirectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is authenticated and on the root path
        if request.user.is_authenticated and request.path == '/':
            # Redirect based on role
            if request.user.is_admin:
                return redirect(reverse('management:admin_dashboard'))
            elif request.user.is_event_manager:
                return redirect(reverse('management:event_manager_dashboard'))
            elif request.user.is_usher:
                return redirect(reverse('checkin:checkin'))
            elif request.user.is_visitor:
                return redirect(reverse('users:profile'))  # Redirecting to visitor profile or dashboard

        # If no conditions match, continue as usual
        response = self.get_response(request)
        return response
