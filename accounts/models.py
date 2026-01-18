from django.db import models
from django.contrib.auth.models import Group


class GroupProfile(models.Model):
    """Metadata for Group, including role type."""

    ROLE_VIEWERS = "Viewers"
    ROLE_EDITORS = "Editors"
    ROLE_MANAGERS = "Managers"
    ROLE_ADMINS = "Admins"

    ROLE_CHOICES = [
        (ROLE_VIEWERS, "Viewers - Read Only"),
        (ROLE_EDITORS, "Editors - View + Edit/Run"),
        (ROLE_MANAGERS, "Managers - View + Edit + Delete"),
        (ROLE_ADMINS, "Admins - Full Access + User Management"),
    ]

    group = models.OneToOneField(
        Group, on_delete=models.CASCADE, related_name="profile"
    )
    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        verbose_name = "Group Profile"
        verbose_name_plural = "Group Profiles"

    def __str__(self):
        return f"{self.group.name} ({self.role_type})"
