from ..models import Recurrence

def get_recurrences(event):
    return Recurrence.objects.filter(event=event)