from django.db import models
from django.conf import settings
from events.models import Event
from registration.models import Ticket


class BadgeTemplate(models.Model):
    FONT_CHOICES = [
        ('Arial', 'Arial'),
        ('Helvetica', 'Helvetica'),
        ('Times New Roman', 'Times New Roman'),
        ('Courier', 'Courier'),
        ('Verdana', 'Verdana'),
        ('Georgia', 'Georgia'),
    ]

    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name="badge_template",
        help_text="Each ticket can have one badge template."
    )
    name = models.CharField(max_length=100)
    width = models.FloatField(help_text="Width of the badge in cm")
    height = models.FloatField(help_text="Height of the badge in cm")
    background_image = models.ImageField(
        upload_to="badge_templates/",
        null=True,
        blank=True,
        help_text="Upload an image to use as the badge background."
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    default_font = models.CharField(
        max_length=50,
        choices=FONT_CHOICES,
        default='Arial',
        help_text="Default font for badge content"
    )

    def __str__(self):
        return f"{self.name} - {self.ticket.name} ({self.ticket.event.name})"


class BadgeContent(models.Model):
    FIELD_CHOICES = [
        ('user__username', 'Username'),
        ('user__email', 'Email'),
        ('user__first_name', 'First Name'),
        ('user__last_name', 'Last Name'),
        ('user__full_name', 'Full Name'),
        ('user__country', 'Country'),
        ('user__title', 'Title'),
        ('user__company', 'Company'),

        ('ticket_type__name', 'Ticket Type'),
        ('event__name', 'Event Name'),
        ('event__location', 'Event Location'),
        ('qr_code__qr_image', 'QR Code'),

    ]

    template = models.ForeignKey(
        BadgeTemplate,
        on_delete=models.CASCADE,
        related_name="contents"
    )
    field_name = models.CharField(
        max_length=50,
        choices=FIELD_CHOICES
    )
    position_x = models.FloatField(help_text="X position in cm")
    position_y = models.FloatField(help_text="Y position in cm")
    font_size = models.IntegerField(default=12, help_text="Font size in points")
    font_color = models.CharField(max_length=7, default='#000000', help_text="Hex color code")
    font_family = models.CharField(
        max_length=50,
        choices=BadgeTemplate.FONT_CHOICES,
        default='Arial'
    )
    is_bold = models.BooleanField(default=False)
    is_italic = models.BooleanField(default=False)
    image_width = models.FloatField(
        null=True,
        blank=True,
        help_text="Width of the image in cm (for QR codes)"
    )
    image_height = models.FloatField(
        null=True,
        blank=True,
        help_text="Height of the image in cm (for QR codes)"
    )

    def get_field_value(self, registration):
        """
        Retrieves the value of the field based on the field_name for a given registration.
        """
        try:
            # Split the field_name to support nested lookups
            field_parts = self.field_name.split('__')
            value = registration

            # Special handling for QR code
            if field_parts[0] == 'qr_code':

                # Now get the QR code image
                value = registration.qr_code
                for part in field_parts[1:]:
                    value = getattr(value, part, None)
                return value

            # Normal field handling
            for part in field_parts:
                value = getattr(value, part, None)
                if callable(value):
                    value = value()
                if value is None:
                    break
            return value
        except AttributeError:
            return f"Field {self.field_name} not found in Registration."
