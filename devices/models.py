import base64
import logging
from typing import Any

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

logger = logging.getLogger(__name__)

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
                condition=~(Q(protocol="telnet") & Q(device_type__endswith="iosxe")),
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
        try:
            genie_dev = self.get_genie_device_object(log_stdout=False)
        except Exception:
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

    def can_connect(self) -> bool:
        success, _, _ = self.test_connection()
        return success

    def test_connection(self) -> tuple[bool, str, str]:
        """
        Tests connectivity to the device.
        Returns (True, "", "") on success.
        Returns (False, error_message, error_category) on failure.
        """
        logger.debug("Testing connection for %s", self.name)
        try:
            self.get_decrypted_password()
            self.get_decrypted_enable_password()
        except (ValidationError, ImproperlyConfigured) as e:
            msg = e.messages[0] if hasattr(e, "messages") else str(e)
            logger.debug("Decryption error for %s: %s", self.name, msg)
            return False, msg, "decryption_error"

        try:
            self.get_genie_device_object(log_stdout=False)
            logger.debug("Connection test successful for %s", self.name)
            return True, "", ""
        except Exception as e:
            logger.debug("Connection test failed for %s: %s", self.name, e)
            return False, str(e), "connection_error"

    def get_genie_device_object(self, log_stdout: bool = True):
        """
        Returns a connected Genie device object.
        Caches the connection for reuse.
        Raises Exception on failure.
        """
        logger.debug(
            "Retrieving Genie device object for %s (PK: %s)", self.name, self.pk
        )
        device = device_connections.get(self.pk)

        if device:
            try:
                if device.is_connected():
                    logger.debug(
                        "Cache hit: %s is already connected. Performing health check.",
                        self.name,
                    )
                    # Minimal check to see if the session is still responsive.
                    # Use a short timeout to avoid hanging if the session is dead.
                    device.execute("show clock", log_stdout=log_stdout, timeout=5)
                    logger.debug("Health check successful for %s", self.name)
                    return device
            except Exception as e:
                logger.debug(
                    "Health check or connection state check failed for %s: %s",
                    self.name,
                    e,
                )

            logger.debug(
                "Cache entry for %s found, but session is unusable.",
                self.name,
            )
            # Stale device object; ensure it is cleaned up before creating a new connection
            try:
                device.disconnect()
            except Exception as e:
                logger.debug(
                    "Error during stale session disconnect for %s: %s",
                    self.name,
                    e,
                )

            # Remove any stale or failed device from the cache before establishing a new connection
            logger.debug(
                "Removing stale/broken connection for %s from cache.", self.name
            )
            device_connections.pop(self.pk, None)

        logger.debug("Establishing new Genie connection to %s", self.name)
        conn_info = self.get_genie_device_dict()
        testbed = load({"devices": conn_info})
        device = testbed.devices[list(conn_info)[0]]

        try:
            device.connect(log_stdout=log_stdout, timeout=15)
            logger.debug("Successfully connected to %s", self.name)
        except Exception as e:
            logger.error("Failed to connect to %s: %s", self.name, e)
            raise

        device_connections[self.pk] = device
        return device

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
