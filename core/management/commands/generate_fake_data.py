import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from faker import Faker
from django.utils import timezone
from django.apps import apps

class Command(BaseCommand):
    help = 'Generate fake data for all models in all apps'

    def __init__(self):
        self.fake = Faker()
        super().__init__()

    def handle(self, *args, **options):
        # Get all models in the project
        all_models = apps.get_models()

        # Loop through each model and generate fake data for it
        for model in all_models:
            self.stdout.write(f'Generating fake data for {model._meta.verbose_name}')
            self.generate_fake_data(model)

    def generate_fake_data(self, model):
        fake = self.fake
        instances = []

        # Generate fake data for models that have specific fields like CustomUser, Permission, LogEntry
        if model == get_user_model():  # Custom User model
            self.generate_fake_user_data(model, instances)
        elif model == Permission:  # Permission model
            self.generate_fake_permission_data(model, instances)
        elif model == LogEntry:  # LogEntry model
            self.generate_fake_log_entry_data(model, instances)
        else:
            self.generate_generic_model_data(model, instances)

        # Bulk create objects for the model
        try:
            model.objects.bulk_create(instances)
            self.stdout.write(self.style.SUCCESS(f'Successfully generated fake data for {model._meta.verbose_name}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to generate data for {model._meta.verbose_name} - {str(e)}'))

    def generate_fake_user_data(self, model, instances):
        roles = list(RoleChoices)
        for _ in range(400):  # Generate 400 users
            role_choice = random.choice(roles)[0]
            user = model(
                username=self.fake.user_name(),
                email=self.fake.email(),
                password=self.fake.password(),
                role=role_choice,
                phone_number=self.fake.phone_number(),
                address=self.fake.address(),
                date_of_birth=self.fake.date_of_birth(),
            )
            instances.append(user)

    def generate_fake_permission_data(self, model, instances):
        permissions = []
        for _ in range(400):  # Generate 400 permissions
            permission_name = self.fake.word()
            while model.objects.filter(name=permission_name).exists():
                permission_name = self.fake.word()  # Ensure unique permission name

            # Generate a random model to assign the permission to
            content_type = random.choice(ContentType.objects.all())

            permission = model(
                name=permission_name,
                content_type=content_type,  # Assigning a valid ContentType instance
                codename=self.fake.word(),
            )
            permissions.append(permission)
        instances.extend(permissions)

    def generate_fake_log_entry_data(self, model, instances):
        for _ in range(400):  # Generate 400 log entries
            # Generate a random model to assign the content_type to
            content_type = random.choice(ContentType.objects.all())

            log_entry = model(
                action_time=timezone.now(),  # Use timezone-aware datetime
                user=random.choice(get_user_model().objects.all()),  # Use CustomUser model here
                content_type=content_type,  # Assigning a valid ContentType instance
                object_id=self.fake.random_number(),
                object_repr=self.fake.word(),
                action_flag=random.choice([1, 2, 3]),  # 1 - ADD, 2 - CHANGE, 3 - DELETE
                change_message=self.fake.sentence(),
            )
            instances.append(log_entry)

    def generate_generic_model_data(self, model, instances):
        # Generic logic to generate fake data for any model
        for _ in range(400):  # Generate 400 instances for generic models
            instance_data = {}
            for field in model._meta.fields:
                field_name = field.name
                field_type = field.get_internal_type()

                # Generate data based on field type
                if field_type == 'CharField':
                    instance_data[field_name] = self.fake.word()
                elif field_type == 'TextField':
                    instance_data[field_name] = self.fake.text()
                elif field_type == 'IntegerField':
                    instance_data[field_name] = self.fake.random_int()
                elif field_type == 'BooleanField':
                    instance_data[field_name] = self.fake.boolean()
                elif field_type == 'DateField':
                    instance_data[field_name] = self.fake.date()
                elif field_type == 'DateTimeField':
                    instance_data[field_name] = timezone.now()  # Use timezone-aware datetime
                elif field_type == 'DecimalField':
                    instance_data[field_name] = self.fake.pydecimal(left_digits=4, right_digits=2, positive=True)
                elif field_type == 'ForeignKey':
                    # Handle ForeignKey (e.g., selecting a related model instance)
                    related_model = field.related_model
                    if related_model.objects.exists():  # Only choose from the related model if it has data
                        instance_data[field_name] = random.choice(related_model.objects.all())
                    else:
                        instance_data[field_name] = None  # Or you can set this to a default value if necessary

            # Create and append the model instance
            instance = model(**instance_data)
            instances.append(instance)
