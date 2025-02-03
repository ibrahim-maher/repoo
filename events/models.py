from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
class Venue(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    capacity = models.IntegerField()

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    venue = models.ForeignKey('Venue', on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    logo = models.ImageField(
        upload_to='event_logos/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'gif'])]
    )

    def save(self, *args, **kwargs):
        if self.is_active:
            Event.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def delete_logo(self):
        if self.logo:
            storage, path = self.logo.storage, self.logo.path
            storage.delete(path)
            self.logo = None

class Recurrence(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    recurrence_type = models.CharField(max_length=50)  # e.g., 'weekly', 'monthly'
    interval = models.IntegerField(default=1)  # e.g., every 1 week/month
    end_date = models.DateTimeField()

    def __str__(self):
        return f"{self.event.name} - {self.recurrence_type}"