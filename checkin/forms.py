from django import forms
from .models import VisitorLog

class ManualCheckInForm(forms.Form):
    registration_id = forms.IntegerField(
        label="Registration ID",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    action = forms.ChoiceField(
        choices=[('checkin', 'Check-in'), ('checkout', 'Check-out')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    admin_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def clean(self):
        cleaned_data = super().clean()
        registration_id = cleaned_data.get("registration_id")
        action = cleaned_data.get("action")

        if registration_id:
            last_log = VisitorLog.objects.filter(registration_id=registration_id).order_by('-timestamp').first()
            if last_log and last_log.action == action:
                raise forms.ValidationError(f"{action} already performed. Please try the opposite action.")
        return cleaned_data
