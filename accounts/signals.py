from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password,
    password_validators_help_texts,
)
from django.core.exceptions import ValidationError
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_superuser_if_none(sender, **kwargs):
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        print("⚠️ No superuser found. Creating one...")

        username = input("Enter admin username: ")

        help_texts = password_validators_help_texts()
        print("\nPassword requirements:")
        for help_text in help_texts:
            print(f" - {help_text}")
        print("")

        while True:
            password = getpass("Enter admin password: ")

            try:
                # Validate the password.
                # passing 'User(username=username)' allows checking against the username
                # (e.g. prohibiting passwords that are too similar to the username).
                # We don't save this user; it's just for validation context.
                validate_password(password, User(username=username))
            except ValidationError as e:
                # If validation fails, print the errors provided by Django
                print("❌ Password validation failed:")
                for error in e.messages:
                    print(f" - {error}")
                continue

            password_verify = getpass("Verify admin password: ")
            if password == password_verify:
                break
            else:
                print("❌ Passwords do not match. Please try again.")

        User.objects.create_superuser(username=username, password=password)
        print("✅ Superuser created!")
