# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from .models import CustomUser
import datetime

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password',
    }))

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user = authenticate(username=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Invalid email or password")
        return self.cleaned_data

    def get_user(self):
        return self.user


from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator, EmailValidator
from .models import CustomUser  # Ensure this points to your custom user model
import uuid


class CustomUserCreationForm(UserCreationForm):
    phone_validator = RegexValidator(
        regex=r'^\+?\d{10,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    email_validator = EmailValidator(message="Please enter a valid email address.")

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'title', 'email', 'role', 'phone_number')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].required = True
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].required = True
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['title'].required = True
        self.fields['title'].widget.attrs.update({'class': 'form-control'})
        self.fields['role'].required = True
        self.fields['role'].widget.attrs.update({'class': 'form-select'})
        self.fields['phone_number'].required = True
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise ValidationError("Phone number is required.")
        self.phone_validator(phone_number)
        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)

        # Generate a unique username based on the email
        email = self.cleaned_data.get('email')
        user.username = slugify(email.split('@')[0]) + str(uuid.uuid4().hex)[:6]

        if commit:
            user.save()
        return user


class EditProfileForm(forms.ModelForm):
    phone_validator = RegexValidator(
        regex=r'^\+?\d{10,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )

    class Meta:
        model = CustomUser
        fields = ['phone_number', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply attributes to ensure consistent styling and edit behavior
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control edit-mode d-none'})


    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        self.phone_validator(phone_number)
        return phone_number

