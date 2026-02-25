from django.apps import AppConfig


class NetworktestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "networktests"

    def ready(self):
        from django.conf import settings
        import os

        custom_dir = getattr(settings, "CUSTOM_TESTCASES_PATH", None)
        if custom_dir:
            try:
                os.makedirs(custom_dir, exist_ok=True)
            except Exception:
                # Might fail due to permissions, which is expected in some environments
                pass
