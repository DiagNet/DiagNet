from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from testgroups.models import TestGroup

User = get_user_model()


class TestGroupPermissionTests(TestCase):
    def setUp(self):
        # Create a superuser to satisfy SuperuserRequiredMiddleware
        User.objects.create_superuser(
            username="admin", password="password123", email="admin@diagnet.com"
        )
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.testgroup = TestGroup.objects.create(name="testgroup1")

    def test_testgroup_page_permission_required(self):
        """Test that testgroups_page redirects if user lacks view_testgroup permission."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("testgroup-page"))
        self.assertRedirects(response, f"/auth/login/?next={reverse('testgroup-page')}")

    def test_list_testgroups_permission_required(self):
        """Test that list_testgroups redirects if user lacks view_testgroup permission."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("testgroup-list"))
        self.assertRedirects(response, f"/auth/login/?next={reverse('testgroup-list')}")

    def test_testgroup_page_with_permission(self):
        """Test that testgroups_page is accessible if user has view_testgroup permission."""
        permission = Permission.objects.get(codename="view_testgroup")
        self.user.user_permissions.add(permission)
        self.client.login(username="testuser", password="password123")

        response = self.client.get(reverse("testgroup-page"))
        self.assertEqual(response.status_code, 200)

    def test_create_testgroup_permission_required(self):
        """Test that create_testgroup returns 403 if user lacks add_testgroup permission (HTMX)."""
        self.client.login(username="testuser", password="password123")
        response = self.client.post(reverse("create-testgroup"), {"name": "newgroup"})
        self.assertEqual(response.status_code, 403)

    def test_delete_testgroup_permission_required(self):
        """Test that delete_testgroup returns 403 if user lacks delete_testgroup permission (HTMX)."""
        self.client.login(username="testuser", password="password123")
        response = self.client.post(reverse("delete-testgroup"), {"name": "testgroup1"})
        self.assertEqual(response.status_code, 403)

    def test_rename_testgroup_permission_required(self):
        """Test that rename_testgroup returns 403 if user lacks change_testgroup permission."""
        self.client.login(username="testuser", password="password123")
        url = reverse("rename-testgroup", kwargs={"name": "testgroup1"})
        response = self.client.post(url, {"name": "newname"})
        self.assertEqual(response.status_code, 403)
