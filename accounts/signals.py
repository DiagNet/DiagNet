import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models.signals import post_delete, post_migrate, post_save
from django.dispatch import receiver

from devices.models import Device
from networktests.models import TestCase, TestResult
from testgroups.models import TestGroup

from .models import GroupProfile

logger = logging.getLogger(__name__)
User = get_user_model()


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


@receiver([post_save, post_delete], sender=User)
def invalidate_superuser_cache(sender, instance, **kwargs):
    """
    Clear the superuser cache whenever any user is created, updated, or deleted.
    This ensures our SuperuserRequiredMiddleware always has fresh data
    without querying the DB on every request.
    """
    cache.delete("superuser_exists")
