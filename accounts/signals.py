from getpass import getpass

from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_superuser_if_none(sender, **kwargs):
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        print("⚠️ No superuser found. Creating one...")
        username = input("Enter admin username: ")
        password = getpass("Enter admin password: ")
        User.objects.create_superuser(username=username, password=password)
        print("✅ Superuser created!")
