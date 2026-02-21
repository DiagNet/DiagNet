"""
ASGI config for diagnet project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.environ.get("DIAGNET_SETTINGS_MODULE", "diagnet.settings"),
)

application = get_asgi_application()
