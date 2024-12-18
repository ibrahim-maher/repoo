# Generated by Django 4.2.16 on 2024-11-25 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='assigned_events',
            field=models.ManyToManyField(blank=True, related_name='assigned_users', to='events.event'),
        ),
    ]