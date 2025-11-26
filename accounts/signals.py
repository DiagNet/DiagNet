import re
from getpass import getpass

from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_superuser_if_none(sender, **kwargs):
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        print("⚠️ No superuser found. Creating one...")

        password_pattern = (
            r"^(?!.*\s)(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*\W)[A-Za-z\d\W]{6,20}$"
        )

        username = input("Enter admin username: ")

        while True:
            password = getpass("Enter admin password: ")
            password_verify = getpass("Verify admin password: ")
            if password == password_verify:
                break
            elif not re.match(password_pattern, password):
                print(
                    "❌ Password must be 6-20 characters long, contain at least one lowercase letter, "
                    "one uppercase letter, one digit, one special character, and have no spaces. Please try again."
                )
            else:
                print("❌ Passwords do not match. Please try again.")

        User.objects.create_superuser(username=username, password=password)
        print("✅ Superuser created!")
