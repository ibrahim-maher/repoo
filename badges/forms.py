import duplicates
from django import forms
from django.db.models import Count
from django.forms import modelformset_factory, BaseModelFormSet

from registration.models import Ticket

from events.models import Event
from .models import BadgeTemplate, BadgeContent
from badges.models import BadgeTemplate




class BadgeTemplateForm(forms.ModelForm):
    event = forms.ModelChoiceField(
        queryset=Event.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select an event first"
    )

    ticket = forms.ModelChoiceField(
        queryset=Ticket.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select a ticket for this badge template"
    )

    class Meta:
        model = BadgeTemplate
        fields = ['name', 'width', 'height', 'background_image', 'default_font']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'background_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'default_font': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'event' in self.data:
            try:
                event_id = int(self.data.get('event'))
                self.fields['ticket'].queryset = Ticket.objects.filter(event_id=event_id)
            except (ValueError, TypeError):
                pass

class BaseBadgeContentFormSet(BaseModelFormSet):
    def clean(self):
        """
        Validate the formset:
        - Ensure at least one field is present
        - Check for duplicate field names
        """
        if any(self.errors):
            return

        if not any(cleaned_data and not cleaned_data.get('DELETE', False)
                   for cleaned_data in self.cleaned_data):
            raise forms.ValidationError('At least one badge content field is required.')

        field_names = []
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue

            cleaned_data = form.cleaned_data
            field_name = cleaned_data.get('field_name')

            if field_name:
                if field_name in field_names:
                    raise forms.ValidationError(
                        f'Field "{form.fields["field_name"].choices[int(field_name)][1]}" cannot be used multiple times.')
                field_names.append(field_name)


class BadgeContentForm(forms.ModelForm):
    class Meta:
        class Meta:
            model = BadgeContent
            fields = '__all__'
        widgets = {
            'field_name': forms.Select(attrs={
                'class': 'form-control'
            }),
            'position_x': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1'
            }),
            'position_y': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1'
            }),
            'font_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'font_color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),
            'font_family': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_bold': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_italic': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


# Create the formset with proper configuration
BadgeContentFormSet = modelformset_factory(
    BadgeContent,
    form=BadgeContentForm,
    fields=['field_name', 'position_x', 'position_y', 'font_size', 'font_color', 'font_family', 'is_bold', 'is_italic'],

    formset=BaseBadgeContentFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)