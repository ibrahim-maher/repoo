from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import connection

class Command(BaseCommand):
    help = "Clear all data from all tables in the database"

    def handle(self, *args, **kwargs):
        all_models = apps.get_models()

        # Disable foreign key checks for SQLite
        self.stdout.write("Disabling foreign key checks...")
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA foreign_keys = OFF;')

        try:
            # Clear data for each model
            for model in all_models:
                model_name = model.__name__
                self.stdout.write(f"Clearing data from table: {model_name}")
                model.objects.all().delete()
        finally:
            # Re-enable foreign key checks for SQLite
            self.stdout.write("Re-enabling foreign key checks...")
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys = ON;')

        self.stdout.write("All data cleared successfully.")
