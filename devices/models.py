from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns
from genie.testbed import load
from django.db.models.functions import Lower
from django.db.models import Q
import netmiko

device_connections = {}


class Device(models.Model):
    DEVICE_TYPES = [
        ("router_ios", "Router (IOS)"),
        ("router_iosxe", "Router (IOSXE)"),
        ("router_iosxr", "Router (IOSXR)"),
        ("switch_ios", "Switch (IOS)"),
        ("switch_iosxe", "Switch (IOSXE)"),
        ("switch_iosxr", "Switch (IOSXR)"),
    ]

    PROTOCOLS = [
        ("ssh", "SSH"),
        ("telnet", "Telnet"),
    ]

    name = models.CharField(
        "Hostname",
        primary_key=True,
        max_length=100,
        unique=True,
    )
    protocol = models.CharField(
        "Protocol",
        choices=PROTOCOLS,
        default="ssh",
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
            models.CheckConstraint(
                check=~(Q(protocol="telnet") & Q(device_type__endswith="iosxe")),
                name="no_telnet_on_iosxe",
                violation_error_message="Telnet is not allowed for IOSXE devices.",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.ip_address})"

    def get_absolute_url(self):
        """Returns the url to access a particular book record."""
        return reverse("device-detail", args=[str(self.name)])

    def get_fields_display(self) -> list[tuple[str, str]]:
        """
        Return a list of (label, value) tuples for UI display.
        Passwords are always masked, choice fields use their display values.
        """
        display_fields = []
        for field in self._meta.fields:
            label = field.verbose_name.title()
            value = getattr(self, field.name)

            # Mask password for display
            if field.name == "password":
                value = "*******"
            # Use human-readable labels for choice fields
            elif field.choices:
                value = getattr(self, f"get_{field.name}_display")()

            display_fields.append((label, value))
        return display_fields

    def get_genie_device_dict(self) -> dict[str, dict[str, Any]]:
        return {
            self.name: {
                "ip": self.ip_address,
                "port": self.port,
                "protocol": self.protocol,
                "username": self.username,
                "password": self.password,
                "os": self.device_type.split("_")[1],
            }
        }

    def get_netmiko_type(self) -> str:
        type_map = {
            "ios": "cisco_ios",
            "iosxe": "cisco_xe",
            "iosxr": "cisco_xr",
        }

        try:
            device_type = self.device_type.split("_")[1]
            ios_type = type_map[device_type]
        except (IndexError, KeyError):
            raise ValueError(f"Unsupported device type: {self.device_type}")

        connection_type = "" if self.protocol == "ssh" else "_telnet"
        return f"{ios_type}{connection_type}"

    def can_connect(self) -> bool:
        device = {
            "device_type": self.get_netmiko_type(),
            "host": self.ip_address,
            "username": self.username,
            "password": self.password,
            # "secret": "enablepass",
            "port": self.port,
        }
        try:
            connection = netmiko.ConnectHandler(**device)
            connection.enable()
            connection.cleanup()
            connection.disconnect()
            return True
        except Exception:
            return False

    def get_genie_device_object(self):
        if (
            self.name in device_connections
            and device_connections[self.name].is_connected()
        ):
            return device_connections[self.name]

        conn_info = self.get_genie_device_dict()
        testbed = load({"devices": conn_info})
        device = testbed.devices[list(conn_info)[0]]

        try:
            device.connect()
            device_connections[self.name] = device
            return device
        except Exception:
            return None
