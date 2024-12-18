from django.db import models

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

    def save(self, *args, **kwargs):
        if self.is_active:
            Event.objects.exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class Recurrence(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    recurrence_type = models.CharField(max_length=50)  # e.g., 'weekly', 'monthly'
    interval = models.IntegerField(default=1)  # e.g., every 1 week/month
    end_date = models.DateTimeField()

    def __str__(self):
        return f"{self.event.name} - {self.recurrence_type}"