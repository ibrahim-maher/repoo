from django import forms
from registration.models import Registration

class ManualCheckInForm(forms.Form):
    registration_id = forms.IntegerField(
        label="Registration ID",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    admin_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def clean_registration_id(self):
        """Validate that the registration ID exists"""
        registration_id = self.cleaned_data.get('registration_id')
        if registration_id:
            try:
                Registration.objects.get(id=registration_id)
            except Registration.DoesNotExist:
                raise forms.ValidationError(f"Registration ID {registration_id} does not exist")
        return registration_id
