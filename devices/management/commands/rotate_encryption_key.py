import getpass
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from devices.models import Device
from cryptography.fernet import Fernet, InvalidToken


class Command(BaseCommand):
    help = "Interactively rotates the encryption key."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("--- Key Rotation Utility ---"))
        self.stdout.write(
            "This tool will decrypt data with an OLD key and re-encrypt it with a NEW key."
        )

        try:
            old_key_input = getpass.getpass(prompt="Enter CURRENT (Old) Key: ").strip()
            if not old_key_input:
                raise CommandError("Old key cannot be empty.")

            new_key_input = getpass.getpass(prompt="Enter NEW Key: ").strip()
            if not new_key_input:
                raise CommandError("New key cannot be empty.")

            confirm_new = getpass.getpass(prompt="Confirm NEW Key: ").strip()
            if new_key_input != confirm_new:
                raise CommandError("New keys do not match.")
        except KeyboardInterrupt:
            self.stdout.write("\nOperation cancelled.")
            return

        try:
            fernet_old = Fernet(old_key_input.encode())
            fernet_new = Fernet(new_key_input.encode())
        except Exception as e:
            raise CommandError(f"Invalid key format: {e}")

        if old_key_input == new_key_input:
            self.stdout.write(
                self.style.WARNING("New key is the same as the old key. Nothing to do.")
            )
            return

        devices = Device.objects.all()
        count = devices.count()
        self.stdout.write(f"\nFound {count} devices. Starting rotation...")

        processed_count = 0

        try:
            with transaction.atomic():
                for device in devices:
                    for field_name in ["password", "enable_password"]:
                        val = getattr(device, field_name)
                        if not val:
                            continue

                        if not val.startswith(Device.ENCRYPTION_PREFIX):
                            raise CommandError(
                                f"Possible data corruption detected: '{field_name}' for device '{device.name}' (ID: {device.id}) "
                                f"is missing the required '{Device.ENCRYPTION_PREFIX}' prefix."
                            )

                        actual_encrypted = val[len(Device.ENCRYPTION_PREFIX) :]
                        try:
                            plain = fernet_old.decrypt(
                                actual_encrypted.encode()
                            ).decode()
                        except (InvalidToken, ValueError):
                            raise CommandError(
                                f"Decryption Error: Cannot decrypt '{field_name}' for device '{device.name}'. "
                                "The old encryption key may be invalid or the data is corrupted."
                            )

                        # Re-encrypt with new key and add prefix
                        new_enc = f"{Device.ENCRYPTION_PREFIX}{fernet_new.encrypt(plain.encode()).decode()}"
                        setattr(device, field_name, new_enc)

                    Device.objects.filter(pk=device.pk).update(
                        password=device.password,
                        enable_password=device.enable_password,
                    )

                    processed_count += 1

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n\nERROR: {e}"))
            self.stdout.write(
                self.style.ERROR(
                    "Transaction rolled back. No data was changed in the database."
                )
            )
            raise CommandError("Key rotation failed.")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n\nSuccess! Rotated {processed_count}/{count} devices."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "IMPORTANT: The database is now encrypted with the NEW KEY."
            )
        )
        self.stdout.write("Update your .env file immediately.\n")
        self.stdout.write(
            "Set DEVICE_ENCRYPTION_KEY to the new key you just entered and store it securely."
        )
