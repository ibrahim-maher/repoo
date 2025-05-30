# Generated by Django 5.1.6 on 2025-04-27 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BadgeContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_name', models.CharField(choices=[('user__username', 'Username'), ('user__email', 'Email'), ('user__first_name', 'First Name'), ('user__last_name', 'Last Name'), ('user__full_name', 'Full Name'), ('user__country', 'Country'), ('user__title', 'Title'), ('user__company', 'Company'), ('ticket_type__name', 'Ticket Type'), ('event__name', 'Event Name'), ('event__location', 'Event Location'), ('qr_code__qr_image', 'QR Code')], max_length=50)),
                ('position_x', models.FloatField(help_text='X position in cm')),
                ('position_y', models.FloatField(help_text='Y position in cm')),
                ('font_size', models.IntegerField(default=12, help_text='Font size in points')),
                ('font_color', models.CharField(default='#000000', help_text='Hex color code', max_length=7)),
                ('font_family', models.CharField(choices=[('Arial', 'Arial'), ('Helvetica', 'Helvetica'), ('Times New Roman', 'Times New Roman'), ('Courier', 'Courier'), ('Verdana', 'Verdana'), ('Georgia', 'Georgia')], default='Arial', max_length=50)),
                ('is_bold', models.BooleanField(default=False)),
                ('is_italic', models.BooleanField(default=False)),
                ('image_width', models.FloatField(blank=True, help_text='Width of the image in cm (for QR codes)', null=True)),
                ('image_height', models.FloatField(blank=True, help_text='Height of the image in cm (for QR codes)', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BadgeTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('width', models.FloatField(help_text='Width of the badge in cm')),
                ('height', models.FloatField(help_text='Height of the badge in cm')),
                ('background_image', models.ImageField(blank=True, help_text='Upload an image to use as the badge background.', null=True, upload_to='badge_templates/')),
                ('default_font', models.CharField(choices=[('Arial', 'Arial'), ('Helvetica', 'Helvetica'), ('Times New Roman', 'Times New Roman'), ('Courier', 'Courier'), ('Verdana', 'Verdana'), ('Georgia', 'Georgia')], default='Arial', help_text='Default font for badge content', max_length=50)),
            ],
        ),
    ]
