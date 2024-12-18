# management/models.py
from django.db import models

class DashboardMetric(models.Model):
    name = models.CharField(max_length=255)
    value = models.IntegerField()

    def __str__(self):
        return self.name

class Report(models.Model):
    name = models.CharField(max_length=255)
    data = models.TextField()

    def __str__(self):
        return self.name