from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import reverse


class SuperuserRequiredMiddleware:
    """
    Middleware that redirects all requests to the setup page if no superuser exists.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setup_url = reverse("setup")

        if (
            request.path.startswith(setup_url)
            or request.path.startswith("/static/")
            or request.path.startswith("/media/")
        ):
            return self.get_response(request)

        superuser_exists = cache.get("superuser_exists")

        if superuser_exists is None:
            User = get_user_model()
            superuser_exists = User.objects.filter(is_superuser=True).exists()

            timeout = 3600 if superuser_exists else 5
            cache.set("superuser_exists", superuser_exists, timeout=timeout)

        if not superuser_exists:
            return redirect(setup_url)

        return self.get_response(request)
