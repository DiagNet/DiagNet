from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns
from genie.testbed import load
from django.db.models.functions import Lower


class Device(models.Model):
    DEVICE_TYPES = [
        ("router_ios", "Router (IOS)"),
        ("router_iosxe", "Router (IOSXE)"),
        ("router_iosxr", "Router (IOSXR)"),
        ("switch_ios", "Switch (IOS)"),
        ("switch_iosxe", "Switch (IOSXE)"),
        ("switch_iosxr", "Switch (IOSXR)"),
    ]

    name = models.CharField(
        "Hostname",
        primary_key=True,
        max_length=100,
        unique=True,
    )
    ip_address = models.GenericIPAddressField("IP Address")
    port = models.IntegerField(
        default=22, validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    device_type = models.CharField(
        "Device Type",
        max_length=20,
        choices=DEVICE_TYPES,
    )
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="name_case_insensitive_unique",
                violation_error_message="Hostname already exists (case insensitive match)",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.ip_address})"

    def get_absolute_url(self):
        """Returns the url to access a particular book record."""
        return reverse("device-detail", args=[str(self.name)])

    def get_genie_device_dict(self) -> dict[str, dict[str, Any]]:
        return {
            self.name: {
                "ip": self.ip_address,
                "port": self.port,
                "protocol": "ssh",
                "username": self.username,
                "password": self.password,
                "os": self.device_type.split("_")[1],
            }
        }

    def can_connect(self) -> bool:
        conn_info = self.get_genie_device_dict()

        __import__("pprint").pprint({"devices": conn_info})
        testbed = load({"devices": conn_info})

        device = testbed.devices[list(conn_info)[0]]
        try:
            device.connect()
            device.disconnect()
            return True
        except Exception:
            return False
