# Generated by Django 3.2.25 on 2025-01-15 12:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0004_remove_registrationfield_created_by'),
        ('badges', '0006_alter_badgecontent_field_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='badgetemplate',
            name='event',
        ),
        migrations.AddField(
            model_name='badgetemplate',
            name='ticket',
            field=models.OneToOneField(default=1, help_text='Each ticket type can have one badge template.', on_delete=django.db.models.deletion.CASCADE, related_name='badge_template', to='registration.ticket'),
        ),
    ]
