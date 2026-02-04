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
            fernet_old = Fernet(old_key_input)
            fernet_new = Fernet(new_key_input)
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
                    plain_password = ""
                    plain_enable = ""

                    if device.password:
                        try:
                            plain_password = fernet_old.decrypt(
                                device.password.encode()
                            ).decode()
                        except InvalidToken:
                            if not device._is_potentially_encrypted(device.password):
                                plain_password = device.password
                            else:
                                raise CommandError(
                                    f"Fatal: Device '{device.name}' (ID: {device.id}) cannot be decrypted with the provided Old Key. Aborting entire operation."
                                )

                    if device.enable_password:
                        try:
                            plain_enable = fernet_old.decrypt(
                                device.enable_password.encode()
                            ).decode()
                        except InvalidToken:
                            if not device._is_potentially_encrypted(
                                device.enable_password
                            ):
                                plain_enable = device.enable_password
                            else:
                                raise CommandError(
                                    f"Fatal: Device '{device.name}' (ID: {device.id}) enable_password cannot be decrypted. Aborting."
                                )

                    new_password_enc = (
                        fernet_new.encrypt(plain_password.encode()).decode()
                        if plain_password
                        else ""
                    )
                    new_enable_enc = (
                        fernet_new.encrypt(plain_enable.encode()).decode()
                        if plain_enable
                        else ""
                    )

                    Device.objects.filter(pk=device.pk).update(
                        password=new_password_enc,
                        enable_password=new_enable_enc,
                    )

                    processed_count += 1

                    if processed_count % 10 == 0:
                        self.stdout.write(
                            f"Processed {processed_count}/{count}...",
                            ending="\r",
                        )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n\nERROR: {e}"))
            self.stdout.write(
                self.style.ERROR(
                    "Transaction rolled back. No data was changed in the database."
                )
            )
            return

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
        self.stdout.write("Update your .env file immediately:\n")
        self.stdout.write(f"DEVICE_ENCRYPTION_KEY={new_key_input}")
