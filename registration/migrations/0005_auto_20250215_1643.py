# Generated by Django 3.2.25 on 2025-02-15 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0004_remove_registrationfield_created_by'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='registrationfield',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='registrationfield',
            name='order',
            field=models.IntegerField(default=0),
        ),
    ]
