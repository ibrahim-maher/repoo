from django.db import models
from django.conf import settings
from django.utils import timezone

from registration.models import Registration


class VisitorLog(models.Model):
    """
    Tracks check-in/check-out activities for event attendees
    """
    registration = models.ForeignKey(
        Registration,
        on_delete=models.CASCADE,
        related_name='visitor_logs'
    )
    action = models.CharField(
        max_length=10,
        choices=[('checkin', 'Check-in'), ('checkout', 'Check-out')]
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, null=True, blank=True)  # New field for exceptions
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_logs'
    )

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.registration.user.username} - {self.action} at {self.timestamp}"

    @property
    def is_valid_checkin_time(self):
        """Check if check-in is within event time"""
        event = self.registration.event
        now = timezone.now()
        return event.start_date <= now <= event.end_date
