from django.core.management.base import BaseCommand
from devices.models import Device


class Command(BaseCommand):
    help = "Encrypts all plain text passwords in the database by re-saving devices."

    def handle(self, *args, **options):
        devices = Device.objects.all()
        count = devices.count()

        self.stdout.write(f"Found {count} devices. Checking encryption...")

        updated_count = 0
        for device in devices:
            # The save method in the model automatically handles encryption
            # if the value is not already encrypted.
            device.save()
            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully processed {updated_count} devices.")
        )
