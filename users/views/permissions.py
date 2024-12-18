# users/views/permissions.py
from django.http import HttpResponseForbidden

def admin_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_admin:
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

def event_manager_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_event_manager:
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

def usher_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_usher:
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func

def visitor_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not request.user.is_visitor:
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped_view_func