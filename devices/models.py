import base64
from typing import Any

import netmiko
import yaml
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.urls import reverse  # To generate URLS by reversing URL patterns
from genie.testbed import load

device_connections = {}


class Device(models.Model):
    ENCRYPTION_PREFIX = "enc:"
    MAX_PLAINTEXT_LENGTH = 256

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
    password = models.CharField(max_length=512)

    enable_password = models.CharField(max_length=512)

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

    def _get_cipher_suite(self):
        key = settings.DEVICE_ENCRYPTION_KEY
        return Fernet(key)

    def _is_fernet_token(self, value: str) -> bool:
        """
        Check if a string strictly follows the Fernet token format.
        - Minimum length check
        - Valid URL-safe base64
        - Correct version byte (0x80)
        """
        if len(value) < 100:
            return False

        try:
            decoded = base64.urlsafe_b64decode(value.encode())
            return len(decoded) >= 73 and decoded[0] == 0x80
        except Exception:
            return False

    def _encrypt_value(self, value: str) -> str:
        """Encrypts the value if it's not already encrypted."""
        if not value:
            return value

        f = self._get_cipher_suite()

        if value.startswith(self.ENCRYPTION_PREFIX):
            actual_value = value[len(self.ENCRYPTION_PREFIX) :]
            if self._is_fernet_token(actual_value):
                try:
                    f.decrypt(actual_value.encode())
                    return value
                except (InvalidToken, ValueError):
                    raise ImproperlyConfigured(
                        "Security Error: Data marked as encrypted looks like a valid token "
                        "but cannot be decrypted with the current key. Please verify DEVICE_ENCRYPTION_KEY."
                    )

        return f"{self.ENCRYPTION_PREFIX}{f.encrypt(value.encode()).decode()}"

    def _decrypt_value(self, value: str) -> str:
        """Decrypts the value."""
        if not value:
            return value

        if not value.startswith(self.ENCRYPTION_PREFIX):
            raise ValidationError(
                f"Decryption Error: Data corruption detected. Stored value is missing the "
                f"required '{self.ENCRYPTION_PREFIX}' prefix."
            )

        actual_value = value[len(self.ENCRYPTION_PREFIX) :]

        if not self._is_fernet_token(actual_value):
            raise ValidationError(
                "Decryption Error: Data marked as encrypted does not follow the expected format."
            )

        f = self._get_cipher_suite()
        try:
            return f.decrypt(actual_value.encode()).decode()
        except (InvalidToken, ValueError):
            raise ImproperlyConfigured(
                "Security Error: Data marked as encrypted looks like a valid token "
                "but cannot be decrypted with the current key. Please verify DEVICE_ENCRYPTION_KEY."
            )

    def get_decrypted_password(self):
        return self._decrypt_value(self.password)

    def get_decrypted_enable_password(self):
        return self._decrypt_value(self.enable_password)

    def save(self, *args, **kwargs):
        self.password = self._encrypt_value(self.password)
        self.enable_password = self._encrypt_value(self.enable_password)
        super().save(*args, **kwargs)

    @property
    def is_plaintext(self) -> bool:
        """Check if any password field is stored as plaintext."""
        for val in [self.password, self.enable_password]:
            if val and not val.startswith(self.ENCRYPTION_PREFIX):
                return True
        return False

    @property
    def is_decryption_error(self) -> bool:
        """Check if credentials are marked as encrypted but cannot be decrypted."""
        for val in [self.password, self.enable_password]:
            if val and val.startswith(self.ENCRYPTION_PREFIX):
                # If it looks like a token but f.decrypt (inside _decrypt_value)
                # would fail, then we have a decryption error.
                try:
                    self._decrypt_value(val)
                except (ImproperlyConfigured, ValidationError):
                    return True
        return False

    @property
    def has_valid_encryption(self) -> bool:
        """Check if both passwords can be decrypted with the current key."""
        try:
            # Must be both prefixed AND decryptable
            if self.is_plaintext:
                return False
            self.get_decrypted_password()
            self.get_decrypted_enable_password()
            return True
        except (ImproperlyConfigured, ValidationError):
            return False

    def __str__(self) -> str:
        return f"{self.name} ({self.ip_address})"

    def get_absolute_url(self):
        """Returns the url to access a particular device record."""
        return reverse("device-detail", args=[str(self.name)])

    def get_all_ips(self) -> list[str]:
        """
        Return all IP addresses (IPv4 + IPv6) from this device using pyATS/Genie.
        Returns [] if unable to connect, no interfaces exist, or all IPs are unassigned.
        """
        genie_dev = self.get_genie_device_object()
        if not genie_dev:
            return []

        ips = set()

        # Safely parse IPv4 interfaces
        try:
            ipv4_data = genie_dev.parse("show ip interface brief") or {}
            interfaces = ipv4_data.get("interface", {})
            if interfaces:
                for info in interfaces.values():
                    ip_addr = info.get("ip_address") or info.get("ip")
                    if ip_addr and ip_addr.lower() != "unassigned":
                        ips.add(ip_addr)
        except Exception:
            # Fail-safe: ignore errors and continue
            pass

        # Safely parse IPv6 interfaces
        try:
            ipv6_data = genie_dev.parse("show ipv6 interface brief") or {}
            interfaces = ipv6_data.get("interface", {})
            if interfaces:
                for info in interfaces.values():
                    ipv6_list = info.get("ipv6", [])
                    if isinstance(ipv6_list, str):
                        ipv6_list = [ipv6_list]
                    for ip in ipv6_list:
                        if ip.lower() != "unassigned":
                            ips.add(ip.split("/")[0])  # remove prefix length
        except Exception:
            # Fail-safe: ignore errors and continue
            pass

        return list(ips)

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
            if field.name in ["password", "enable_password"]:
                value = "*******"
            # Use human-readable labels for choice fields
            elif field.choices:
                value = getattr(self, f"get_{field.name}_display")()

            display_fields.append((label, value))
        return display_fields

    def get_genie_device_dict(self) -> dict[str, dict[str, Any]]:
        return {
            self.name: {
                "os": self.device_type.split("_")[1],
                "connections": {
                    "cli": {
                        "protocol": self.protocol,
                        "ip": self.ip_address,
                        "port": self.port,
                    },
                },
                "credentials": {
                    "default": {
                        "username": self.username,
                        "password": self.get_decrypted_password(),
                    },
                    "enable": {
                        "password": self.get_decrypted_enable_password(),
                    },
                },
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
            raise ValidationError(f"Unsupported device type: {self.device_type}")

        connection_type = "" if self.protocol == "ssh" else "_telnet"
        return f"{ios_type}{connection_type}"

    def can_connect(self) -> bool:
        try:
            device = {
                "device_type": self.get_netmiko_type(),
                "host": self.ip_address,
                "username": self.username,
                "password": self.get_decrypted_password(),
                "secret": self.get_decrypted_enable_password(),
                "port": self.port,
            }
            connection = netmiko.ConnectHandler(**device)
            connection.enable()
            connection.cleanup()
            connection.disconnect()
            return True
        except Exception:
            return False

    def test_connection(self) -> tuple[bool, str, str]:
        """
        Tests connectivity to the device.
        Returns (True, "", "") on success.
        Returns (False, error_message, error_category) on failure.
        """
        try:
            device_params = {
                "device_type": self.get_netmiko_type(),
                "host": self.ip_address,
                "username": self.username,
                "password": self.get_decrypted_password(),
                "secret": self.get_decrypted_enable_password(),
                "port": self.port,
            }
            connection = netmiko.ConnectHandler(**device_params)
            connection.enable()
            connection.cleanup()
            connection.disconnect()
            return True, "", ""
        except (ValidationError, ImproperlyConfigured) as e:
            msg = e.messages[0] if hasattr(e, "messages") else str(e)
            return False, msg, "decryption_error"
        except Exception as e:
            return False, str(e), "connection_error"

    def get_genie_device_object(self):
        device = device_connections.get(self.name)

        if device:
            try:
                if device.is_connected():
                    device.execute("show clock")
                    return device
                else:
                    # Stale device object; ensure it is cleaned up before creating a new connection
                    try:
                        device.disconnect()
                    except Exception:
                        pass
            except Exception:
                try:
                    device.disconnect()
                except Exception:
                    pass
            # Remove any stale or failed device from the cache before establishing a new connection
            device_connections.pop(self.name, None)

        try:
            conn_info = self.get_genie_device_dict()
            testbed = load({"devices": conn_info})
            device = testbed.devices[list(conn_info)[0]]
            device.connect()
            device_connections[self.name] = device
            return device
        except Exception:
            return None

    def export_to_yaml(self):
        """
        Exports the device to a yaml format.

        The output yaml structure looks like this:

        <hostname>
            protocol: <protocol>
            ip_address: <ip_address>
            port: <port>
            device_type: <device_type>
            username: <username>
            password: <encrypted_password>
            enable_password: <encrypted_enable_password>

        Note: Credentials are exported in their encrypted format (prefixed with 'enc:').
        To be usable after import, the destination system must use the same
        DEVICE_ENCRYPTION_KEY.
        """

        data = {
            self.name: {
                field.name: getattr(self, field.name)
                for field in self._meta.fields
                if field.name != "name"
            }
        }

        return yaml.dump(data, sort_keys=False)
