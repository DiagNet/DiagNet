from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse


class SuperuserRequiredMiddleware:
    """
    Middleware that redirects all requests to the setup page if no superuser exists.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow access to setup, static files, and media files without needing
        # a superuser
        setup_url = reverse("setup")
        if (
            request.path.startswith(setup_url)
            or request.path.startswith("/static/")
            or request.path.startswith("/media/")
        ):
            return self.get_response(request)

        if not User.objects.filter(is_superuser=True).exists():
            return redirect(setup_url)

        return self.get_response(request)
