from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()


class DashboardPermissionTests(TestCase):
    def setUp(self):
        # Create a superuser to satisfy SuperuserRequiredMiddleware
        User.objects.create_superuser(
            username="admin", password="password123", email="admin@diagnet.dev"
        )
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )

    def test_dashboard_index_permission_required(self):
        """Test that dashboard index redirects if user lacks required permissions."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("dashboard"))
        # Dashboard index requires: networktests.view_testcase, networktests.view_testresult, testgroups.view_testgroup
        self.assertRedirects(response, f"/auth/login/?next={reverse('dashboard')}")

    def test_dashboard_data_permission_required(self):
        """Test that dashboard data redirects if user lacks required permissions."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("dashboard-data"))
        self.assertRedirects(response, f"/auth/login/?next={reverse('dashboard-data')}")

    def test_dashboard_index_with_permissions(self):
        """Test that dashboard index is accessible if user has all required permissions."""
        perms = [
            Permission.objects.get(
                codename="view_testcase", content_type__app_label="networktests"
            ),
            Permission.objects.get(
                codename="view_testresult", content_type__app_label="networktests"
            ),
            Permission.objects.get(
                codename="view_testgroup", content_type__app_label="testgroups"
            ),
        ]
        self.user.user_permissions.add(*perms)
        self.client.login(username="testuser", password="password123")

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
