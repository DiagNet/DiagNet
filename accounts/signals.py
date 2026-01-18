import logging
from getpass import getpass

from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.password_validation import (
    password_validators_help_texts,
    validate_password,
)
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from devices.models import Device
from networktests.models import TestCase, TestResult
from testgroups.models import TestGroup

from .models import GroupProfile

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def create_superuser_if_none(sender, **kwargs):
    if sender.name != "accounts":
        return

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


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """Create default groups with permissions after migration."""

    def get_perms(model_class, actions):
        """Get permission objects for a model and actions."""
        ct = ContentType.objects.get_for_model(model_class)
        return list(
            Permission.objects.filter(
                content_type=ct,
                codename__in=[f"{a}_{model_class._meta.model_name}" for a in actions],
            )
        )

    # 1. Viewers (Read Only)
    viewer_permissions = []
    for model_class in [Device, TestCase, TestResult, TestGroup]:
        viewer_permissions.extend(get_perms(model_class, ["view"]))

    # Only proceed if all permissions exist (4 view permissions for 4 models)
    if len(viewer_permissions) != 4:
        return

    # 2. Editors (Viewers + Edit/Run)
    editor_permissions = list(viewer_permissions)
    for model_class in [Device, TestCase, TestGroup]:
        editor_permissions.extend(get_perms(model_class, ["add", "change"]))
    editor_permissions.extend(
        get_perms(TestResult, ["add"])
    )  # 'add' needed to run tests

    # 3. Managers (Editors + Delete)
    manager_permissions = list(editor_permissions)
    for model_class in [Device, TestCase, TestGroup, TestResult]:
        manager_permissions.extend(get_perms(model_class, ["delete"]))

    # 4. Admins (Managers + User Management)
    admin_permissions = list(manager_permissions)
    admin_permissions.extend(get_perms(User, ["add", "change", "delete", "view"]))
    admin_permissions.extend(get_perms(Group, ["add", "change", "delete", "view"]))

    role_permissions = {
        "Viewers": viewer_permissions,
        "Editors": editor_permissions,
        "Managers": manager_permissions,
        "Admins": admin_permissions,
    }

    for role_name, permissions in role_permissions.items():
        group, created = Group.objects.get_or_create(name=role_name)

        if created:
            # Only create default groups if no other groups exist
            if Group.objects.exclude(name__in=role_permissions.keys()).exists():
                group.delete()
                continue

            group.permissions.set(permissions)
            GroupProfile.objects.update_or_create(
                group=group, defaults={"role_type": role_name}
            )
            logger.info(
                "Created default group '%s' with %d permissions.",
                role_name,
                len(permissions),
            )
        else:
            # Update permissions for existing default groups only if changed
            current_permissions = set(group.permissions.all())
            new_permissions = set(permissions)
            if current_permissions != new_permissions:
                group.permissions.set(permissions)
                logger.info(
                    "Updated default group '%s' with %d permissions.",
                    role_name,
                    len(permissions),
                )
            GroupProfile.objects.update_or_create(
                group=group, defaults={"role_type": role_name}
            )
