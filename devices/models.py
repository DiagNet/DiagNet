from django.db import models


class Device(models.Model):
    DEVICE_TYPES = [
        ("router", "Router"),
        ("switch", "Switch"),
        ("server", "Server"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"
