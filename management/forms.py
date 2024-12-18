# management/forms.py
from django import forms
from .models import DashboardMetric, Report

class DashboardMetricForm(forms.ModelForm):
    class Meta:
        model = DashboardMetric
        fields = ['name', 'value']

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['name', 'data']