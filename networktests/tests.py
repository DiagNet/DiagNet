import os
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import CustomTestTemplate
from .testcases.base import DiagNetTest
from .utils import (
    get_all_available_test_classes,
    get_builtin_test_class_names,
    get_test_class_from_file,
    is_valid_test_class,
    sanitize_filename,
    sync_custom_testcases,
)

User = get_user_model()


class CustomTemplateTests(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Create a dummy test file
        self.test_file_path = os.path.join(self.test_dir, "MyCustomTest.py")
        with open(self.test_file_path, "w") as f:
            f.write(
                """from networktests.testcases.base import DiagNetTest


class MyCustomTest(DiagNetTest):
    _params = []

    def test_example(self):
        return True
"""
            )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_custom_templates_respect_settings(self):
        with override_settings(
            CUSTOM_TESTCASES_PATH=self.test_dir, ENABLE_CUSTOM_TESTCASES=False
        ):
            # Even if it exists and is enabled in DB, it should not be loaded if global setting is False
            CustomTestTemplate.objects.create(
                class_name="MyCustomTest",
                file_name="MyCustomTest.py",
                is_enabled=True,
            )
            classes = get_all_available_test_classes()
            self.assertNotIn("MyCustomTest", classes)

    def test_custom_templates_respect_enable_flag(self):
        with override_settings(
            CUSTOM_TESTCASES_PATH=self.test_dir, ENABLE_CUSTOM_TESTCASES=True
        ):
            # Not in DB yet
            classes = get_all_available_test_classes()
            self.assertNotIn("MyCustomTest", classes)

            # In DB but disabled
            template = CustomTestTemplate.objects.create(
                class_name="MyCustomTest",
                file_name="MyCustomTest.py",
                is_enabled=False,
            )
            classes = get_all_available_test_classes()
            self.assertNotIn("MyCustomTest", classes)

            # In DB and enabled
            template.is_enabled = True
            template.save()
            classes = get_all_available_test_classes()
            self.assertIn("MyCustomTest", classes)

    def test_sync_function(self):
        with override_settings(CUSTOM_TESTCASES_PATH=self.test_dir):
            count, error = sync_custom_testcases()
            self.assertEqual(count, 1)
            self.assertIsNone(error)
            self.assertTrue(
                CustomTestTemplate.objects.filter(class_name="MyCustomTest").exists()
            )

    def test_sync_non_existent_directory(self):
        with override_settings(CUSTOM_TESTCASES_PATH="/non/existent/path/12345"):
            count, error = sync_custom_testcases()
            self.assertEqual(count, 0)
            self.assertIn("does not exist", error)

    def test_get_class_unreadable_file(self):
        # Create an unreadable file
        unreadable_path = os.path.join(self.test_dir, "Unreadable.py")
        with open(unreadable_path, "w") as f:
            f.write("class Unreadable: pass")
        os.chmod(unreadable_path, 0o000)

        try:
            cls = get_test_class_from_file(unreadable_path, "Unreadable")
            self.assertIsNone(cls)
        finally:
            os.chmod(unreadable_path, 0o644)

    def test_get_class_invalid_python(self):
        invalid_path = os.path.join(self.test_dir, "Invalid.py")
        with open(invalid_path, "w") as f:
            f.write("this is not valid python code!!!")

        cls = get_test_class_from_file(invalid_path, "Invalid")
        self.assertIsNone(cls)

    def test_sync_cleans_up_stale_entries(self):
        """Test that sync removes database entries for files that no longer exist."""
        with override_settings(CUSTOM_TESTCASES_PATH=self.test_dir):
            # First sync to create entry
            sync_custom_testcases()
            self.assertTrue(
                CustomTestTemplate.objects.filter(class_name="MyCustomTest").exists()
            )

            # Create another file and sync
            another_file = os.path.join(self.test_dir, "AnotherTest.py")
            with open(another_file, "w") as f:
                f.write(
                    """from networktests.testcases.base import DiagNetTest


class AnotherTest(DiagNetTest):
    _params = []

    def test_example(self):
        return True
"""
                )
            sync_custom_testcases()
            self.assertEqual(CustomTestTemplate.objects.count(), 2)

            # Remove the original file and sync again
            os.remove(self.test_file_path)
            sync_custom_testcases()

            # MyCustomTest should be removed from DB
            self.assertFalse(
                CustomTestTemplate.objects.filter(class_name="MyCustomTest").exists()
            )
            self.assertTrue(
                CustomTestTemplate.objects.filter(class_name="AnotherTest").exists()
            )


class SecurityTests(TestCase):
    """Tests for security-related functionality."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_sanitize_filename_removes_path_traversal(self):
        """Test that path traversal attempts are sanitized."""
        self.assertEqual(sanitize_filename("../../../etc/passwd"), "passwd")
        self.assertEqual(
            sanitize_filename("..\\..\\windows\\system32\\config"), "config"
        )
        self.assertEqual(sanitize_filename("/absolute/path/file.py"), "file.py")
        self.assertEqual(sanitize_filename("simple.py"), "simple.py")
        self.assertEqual(sanitize_filename("./relative.py"), "relative.py")

    def test_sanitize_filename_removes_null_bytes(self):
        """Test that null bytes are removed from filenames."""
        self.assertEqual(sanitize_filename("file\x00.py"), "file.py")
        self.assertEqual(sanitize_filename("test\x00name\x00.py"), "testname.py")

    def test_builtin_names_are_detected(self):
        """Test that built-in test class names are properly detected."""
        builtin_names = get_builtin_test_class_names()
        # Check that some known built-in test classes are detected
        self.assertIn("Ping", builtin_names)
        self.assertIn("OSPF_Adjacency", builtin_names)
        # base.py and __init__.py should not be included
        self.assertNotIn("base", builtin_names)
        self.assertNotIn("__init__", builtin_names)

    def test_custom_cannot_override_builtin(self):
        """Test that custom templates cannot override built-in test classes."""
        # Create a file named after a built-in test class
        ping_override_path = os.path.join(self.test_dir, "Ping.py")
        with open(ping_override_path, "w") as f:
            f.write(
                """from networktests.testcases.base import DiagNetTest


class Ping(DiagNetTest):
    _params = []

    def test_malicious(self):
        return True
"""
            )

        with override_settings(
            CUSTOM_TESTCASES_PATH=self.test_dir, ENABLE_CUSTOM_TESTCASES=True
        ):
            # Sync should skip the Ping file
            count, error = sync_custom_testcases()
            self.assertEqual(count, 0)
            self.assertIn("Ping", error)  # Warning about conflict

            # Even if someone manually creates a DB entry, it should not be loaded
            CustomTestTemplate.objects.create(
                class_name="Ping",
                file_name="Ping.py",
                is_enabled=True,
            )
            classes = get_all_available_test_classes()

            # Ping should be the built-in, not custom
            self.assertIn("Ping", classes)
            self.assertEqual(classes["Ping"]["source"], "built-in")

    def test_sync_skips_builtin_conflicts(self):
        """Test that sync reports files that conflict with built-ins."""
        # Create files that conflict with built-ins
        for name in ["Ping", "OSPF_Adjacency"]:
            path = os.path.join(self.test_dir, f"{name}.py")
            with open(path, "w") as f:
                f.write(f"class {name}: pass\n")

        with override_settings(CUSTOM_TESTCASES_PATH=self.test_dir):
            count, error = sync_custom_testcases()
            self.assertEqual(count, 0)
            self.assertIsNotNone(error)
            self.assertIn("Ping", error)
            self.assertIn("OSPF_Adjacency", error)


class TestClassValidationTests(TestCase):
    """Tests for test class interface validation."""

    def test_valid_test_class(self):
        """Test that a subclass of DiagNetTest is considered valid."""

        class ValidTest(DiagNetTest):
            _params = []

            def test_example(self):
                return True

        self.assertTrue(is_valid_test_class(ValidTest))

    def test_valid_test_class_with_optional_attrs(self):
        """Test that a class with optional _mutually_exclusive_parameters is valid."""

        class ValidTest(DiagNetTest):
            _params = []
            _mutually_exclusive_parameters = []

            def test_example(self):
                return True

        self.assertTrue(is_valid_test_class(ValidTest))

    def test_not_subclass_of_diagnettest(self):
        """Test that a class not inheriting from DiagNetTest is invalid."""

        class InvalidTest:
            _params = []

            def run(self, **kwargs):
                return {"result": "PASS"}

        self.assertFalse(is_valid_test_class(InvalidTest))

    def test_class_without_test_methods_is_valid(self):
        """Test that a DiagNetTest subclass without test methods is still valid (structure-wise)."""

        class ValidTest(DiagNetTest):
            _params = []

        self.assertTrue(is_valid_test_class(ValidTest))

    def test_invalid_class_not_loaded(self):
        """Test that invalid classes are not loaded into available test classes."""
        test_dir = tempfile.mkdtemp()
        try:
            # Create a file with a class missing required interface
            invalid_path = os.path.join(test_dir, "InvalidTest.py")
            with open(invalid_path, "w") as f:
                f.write("class InvalidTest:\n    pass\n")

            with override_settings(
                CUSTOM_TESTCASES_PATH=test_dir, ENABLE_CUSTOM_TESTCASES=True
            ):
                # Create DB entry and enable it
                CustomTestTemplate.objects.create(
                    class_name="InvalidTest",
                    file_name="InvalidTest.py",
                    is_enabled=True,
                )
                classes = get_all_available_test_classes()
                # Should not be loaded because it doesn't have required interface
                self.assertNotIn("InvalidTest", classes)
        finally:
            shutil.rmtree(test_dir)


class NetworkTestsPermissionTests(TestCase):
    def setUp(self):
        # Create a superuser to satisfy SuperuserRequiredMiddleware
        User.objects.create_superuser(
            username="admin", password="password123", email="admin@diagnet.dev"
        )
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )

    def test_index_permission_required(self):
        """Test that networktests index redirects if user lacks view_testcase permission."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("networktests-page"))
        self.assertRedirects(
            response, f"/auth/login/?next={reverse('networktests-page')}"
        )

    def test_create_test_page_permission_required(self):
        """Test that create test page redirects if user lacks add_testcase permission."""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("test-page"))
        self.assertRedirects(response, f"/auth/login/?next={reverse('test-page')}")

    def test_run_testcase_permission_required(self):
        """Test that run testcase returns 403 if user lacks add_testresult permission."""
        self.client.login(username="testuser", password="password123")
        # Using a dummy PK 999
        url = reverse("tests-run", kwargs={"pk": 999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
