from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from devices.models import Device

User = get_user_model()


class DevicePermissionTests(TestCase):
    def setUp(self):
        # Create a superuser to satisfy SuperuserRequiredMiddleware
        User.objects.create_superuser(
            username="admin", password="password123", email="admin@diagnet.dev"
        )
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.device = Device.objects.create(
            name="test-device",
            ip_address="192.168.1.1",
            device_type="cisco_ios",
            protocol="ssh",
            username="admin",
            password="password",
        )

    def test_index_permission_required(self):
        """Test that devices index redirects if user lacks view_device permission."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("devices-page"))
        # FBVs using @permission_required redirect by default
        self.assertRedirects(response, f"/auth/login/?next={reverse('devices-page')}")

    def test_index_with_permission(self):
        """Test that devices index is accessible if user has view_device permission."""
        permission = Permission.objects.get(codename="view_device")
        self.user.user_permissions.add(permission)
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("devices-page"))
        self.assertEqual(response.status_code, 200)

    def test_device_create_permission_required(self):
        """Test that device create returns 403 if user lacks add_device permission."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("device-create"))
        # CBVs using PermissionRequiredMixin return 403 for authenticated users by default
        self.assertEqual(response.status_code, 403)

    def test_device_update_permission_required(self):
        """Test that device update returns 403 if user lacks change_device permission."""
        self.client.login(username="testuser", password="password123")
        url = reverse("device-update", kwargs={"pk": self.device.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_device_delete_permission_required(self):
        """Test that device delete returns 403 if user lacks delete_device permission."""
        self.client.login(username="testuser", password="password123")
        url = reverse("device-delete", kwargs={"pk": self.device.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_device_check_permission_required(self):
        """Test that device check returns 403 if user lacks add_testresult permission."""
        self.client.login(username="testuser", password="password123")
        url = reverse("device-check", kwargs={"pk": self.device.pk})
        response = self.client.get(url)
        # FBV returns 403 because raise_exception=True
        self.assertEqual(response.status_code, 403)
