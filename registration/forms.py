from django import forms
from django.core.validators import RegexValidator

from .models import Ticket, RegistrationField
class UserSearchForm(forms.Form):
    search_query = forms.CharField(max_length=100, required=True)




class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),

        }

class RegistrationFieldForm(forms.ModelForm):
    options = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        help_text="Enter dropdown options separated by commas"
    )

    class Meta:
        model = RegistrationField
        fields = ['field_name', 'field_type', 'is_required']
        widgets = {
            'field_name': forms.TextInput(attrs={'class': 'form-control'}),
            'field_type': forms.Select(attrs={'class': 'form-select'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing field with dropdown type, populate options
        self.fields['options'].widget = forms.HiddenInput()

        if self.instance and self.instance.field_type == 'dropdown':
            self.fields['options'].initial = self.instance.options


class DynamicRegistrationForm(forms.Form):
    def __init__(self, event, *args, **kwargs):
        """
        Dynamically generate fields based on the event's associated registration fields.
        """
        super().__init__(*args, **kwargs)
        # Get custom fields for the event
        custom_fields = RegistrationField.objects.filter(event=event)

        for field in custom_fields:
            # Dynamically add form fields based on the field type
            if field.field_type == 'text':
                self.fields[field.field_name] = forms.CharField(
                    label=field.field_name, required=field.is_required
                )
            elif field.field_type == 'email':
                self.fields[field.field_name] = forms.EmailField(
                    label=field.field_name, required=field.is_required
                )
            elif field.field_type == 'number':
                self.fields[field.field_name] = forms.IntegerField(
                    label=field.field_name, required=field.is_required
                )
            elif field.field_type == 'dropdown':
                options = field.options.split(',') if field.options else []
                self.fields[field.field_name] = forms.ChoiceField(
                    label=field.field_name,
                    choices=[(opt.strip(), opt.strip()) for opt in options],
                    required=field.is_required
                )
            elif field.field_type == 'checkbox':
                self.fields[field.field_name] = forms.BooleanField(
                    label=field.field_name, required=field.is_required
                )
