# system/duplicate_check.py
from registration.models import Registration

def check_duplicate_registration(user, event):
    return Registration.objects.filter(user=user, event=event).exists()