from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class SetupWizardTest(TestCase):
    def setUp(self):
        """Runs before every single test method."""
        cache.clear()

    def test_setup_redirects_if_no_superuser(self):
        """Test that any page redirects to setup if no superuser exists."""
        response = self.client.get(reverse("dashboard"), follow=True)
        self.assertRedirects(response, reverse("setup"))
        self.assertTemplateUsed(response, "accounts/setup.html")

    def test_setup_page_accessible_without_login(self):
        """Test that the setup page is accessible when no superuser exists."""
        response = self.client.get(reverse("setup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/setup.html")

    def test_superuser_creation_via_setup(self):
        """Test creating a superuser via the setup page."""
        setup_url = reverse("setup")
        data = {
            "username": "admin",
            "email": "admin@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        response = self.client.post(setup_url, data, follow=True)

        # Should redirect to dashboard after success
        self.assertRedirects(response, reverse("dashboard"))

        # Superuser should exist
        self.assertTrue(
            User.objects.filter(username="admin", is_superuser=True).exists()
        )

        # Should be logged in
        user = User.objects.get(username="admin")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_setup_redirects_to_login_if_superuser_exists(self):
        """Test that setup page redirects to login if a superuser already exists."""
        User.objects.create_superuser(username="existingadmin", password="password123")

        response = self.client.get(reverse("setup"))
        self.assertRedirects(response, reverse("login"))

    def test_no_redirect_to_setup_if_superuser_exists(self):
        """Test that there is no redirect to setup if a superuser exists."""
        User.objects.create_superuser(username="existingadmin", password="password123")

        # Log in
        self.client.login(username="existingadmin", password="password123")

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, "accounts/setup.html")


class SetupConcurrencyTest(TestCase):
    def test_setup_blocks_concurrent_requests(self):
        """Test that the setup view gracefully rejects requests if the lock is held."""

        # adds a lock in cache to test race condition
        with patch("django.core.cache.cache.add", return_value=False):
            data = {
                "username": "admin_race",
                "email": "admin@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            }
            response = self.client.post(reverse("setup"), data, follow=True)

            self.assertEqual(response.status_code, 200)

            messages = list(response.context.get("messages", []))
            self.assertTrue(
                any("Setup is currently processing" in str(m) for m in messages),
                "Expected concurrency error message not found.",
            )

            self.assertEqual(User.objects.count(), 0)
