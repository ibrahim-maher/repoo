from django.db import models
from events.models import Event
import json
from io import BytesIO
from django.core.files.storage import default_storage
from django.conf import settings
import os
import qrcode  # Import qrcode without alias


class Ticket(models.Model):
    """
    Defines different types of tickets for an event, e.g., General, VIP, Early Bird.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ticket_types")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use AUTH_USER_MODEL
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} - {self.event.name}"


class RegistrationField(models.Model):
    """
    Defines custom fields for event registration forms.
    """
    FIELD_TYPES = [
        ('text', 'Text'),
        ('email', 'Email'),
        ('number', 'Number'),
        ('dropdown', 'Dropdown'),
        ('checkbox', 'Checkbox'),
    ]

    DEFAULT_FIELDS = [
        {'field_name': 'First Name', 'field_type': 'text', 'is_required': True},
        {'field_name': 'Last Name', 'field_type': 'text', 'is_required': True},
        {'field_name': 'Email', 'field_type': 'email', 'is_required': True},
        {'field_name': 'Phone Number', 'field_type': 'number', 'is_required': True},
        {'field_name': 'Title', 'field_type': 'text', 'is_required': True},
        {'field_name': 'Company Name', 'field_type': 'text', 'is_required': False},
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="custom_fields")
    field_name = models.CharField(max_length=50)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=True)
    options = models.TextField(null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.field_name} - {self.event.name}"


class Registration(models.Model):
    """
    Represents a registration for an event.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ticket_type = models.ForeignKey(Ticket, on_delete=models.SET_NULL, null=True, blank=True)
    registration_data = models.TextField(null=True, blank=True, default='{}')  # To store dynamic form data as JSON
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.event.name}"

    def get_registration_data(self):
        """
        Deserialize registration_data into a Python dictionary.
        """
        try:
            return json.loads(self.registration_data)
        except json.JSONDecodeError:
            return {}

    def set_registration_data(self, data):
        """
        Serialize a Python dictionary into registration_data.
        """
        self.registration_data = json.dumps(data)


class QRCode(models.Model):
    """
    Represents a QR code generated for a registration.
    """
    registration = models.OneToOneField(
        Registration, on_delete=models.CASCADE, related_name="qr_code"
    )
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, null=True, blank=True, related_name="qr_codes"
    )
    qr_image = models.ImageField(upload_to="qr_codes/", blank=True, null=True)

    def generate_qr_code(self):
        """
        Generates a QR code containing registration details and saves it to a specific path.
        """
        # Safely access ticket type from the associated ticket
        ticket_name = self.ticket.name if self.ticket else "No Ticket"

        # Data to encode in the QR code
        qr_data = {
            "user_id": self.registration.user.id,
            "event_id": self.registration.event.id,
            "registration_id": self.registration.id,
            "ticket_type": ticket_name,
        }

        # Create the QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Generate the image
        qr_image = qr.make_image(fill="black", back_color="white")

        # Define the filename and path for the QR code
        qr_code_filename = f"qr_{self.registration.id}.png"
        file_path = os.path.join("custom_qr_codes", qr_code_filename)  # Relative path in the bucket

        # Save the image to a BytesIO buffer
        buffer = BytesIO()
        qr_image.save(buffer, format="PNG")
        buffer.seek(0)  # Reset the buffer position to the beginning

        try:
            # Upload the image to DigitalOcean Spaces
            default_storage.save(file_path, buffer)
            print(f"QR code uploaded successfully: {file_path}")
        except Exception as e:
            print(f"Error uploading QR code to DigitalOcean Spaces: {e}")
            raise
        finally:
            # Close the buffer
            buffer.close()

        # Save the file path to the qr_image field
        self.qr_image.name = f"custom_qr_codes/{qr_code_filename}"
