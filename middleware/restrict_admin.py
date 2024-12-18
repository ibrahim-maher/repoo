from django.shortcuts import redirect
from django.urls import reverse

class RestrictAdminMiddleware:
    """
    Middleware to restrict access to the Django admin interface for unauthorized users.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Redirect if accessing /admin/ and the user is not a superuser
        if request.path.startswith('/admin/') and not request.user.is_superuser:
            return redirect(reverse('management:dashboard'))  # Redirect to your custom dashboard
        return self.get_response(request)
