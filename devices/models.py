from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Device(models.Model):
    DEVICE_TYPES = [
        ("router_ios", "Router (IOS)"),
        ("router_iosxe", "Router (IOSXE)"),
        ("router_iosxr", "Router (IOSXR)"),
        ("switch_ios", "Switch (IOS)"),
        ("switch_iosxe", "Switch (IOSXE)"),
        ("switch_iosxr", "Switch (IOSXR)"),
    ]

    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(verbose_name="IP Address")
    port = models.IntegerField(
        default=22, validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    device_type = models.CharField(
        max_length=20, choices=DEVICE_TYPES, verbose_name="Device Type"
    )
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"
