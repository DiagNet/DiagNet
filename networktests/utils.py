import importlib
import importlib.resources
import importlib.util
import logging
import os
from pathlib import Path

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

PACKAGE = "networktests.testcases"

# Cache for loaded test classes to avoid redundant execution
_test_class_load_cache = {}


def is_valid_test_class(cls):
    """
    Check if a class has the required test class interface.
    Returns True if the class is a subclass of DiagNetTest.

    Custom test classes should inherit from DiagNetTest which provides
    the run() method and test discovery logic. The custom class only
    needs to define _params and test_* methods.
    """
    from networktests.testcases.base import DiagNetTest

    try:
        return isinstance(cls, type) and issubclass(cls, DiagNetTest)
    except TypeError:
        return False


def sanitize_filename(filename):
    """
    Sanitize a filename to prevent path traversal attacks.
    Returns only the base name, stripping any directory components.
    Handles both Unix (/) and Windows (\\) path separators.
    """
    # Handle both Unix and Windows path separators
    # First normalize Windows backslashes to forward slashes
    normalized = filename.replace("\\", "/")
    # Get only the basename to prevent path traversal
    safe_name = os.path.basename(normalized)
    # Additional safety: remove any null bytes or other dangerous characters
    safe_name = safe_name.replace("\x00", "")
    return safe_name


def is_within_directory(directory, target):
    """
    Check if a target path is located within a specific directory.
    Prevents path traversal attacks.
    """
    try:
        abs_directory = Path(directory).resolve()
        abs_target = Path(target).resolve()
        return abs_target.is_relative_to(abs_directory)
    except (ValueError, RuntimeError):
        return False


def get_safe_custom_template_path(filename):
    """
    Construct a safe absolute path for a custom template file.
    Ensures the path is within the configured custom testcases directory.
    """
    custom_dir_str = getattr(settings, "CUSTOM_TESTCASES_PATH", None)
    if not custom_dir_str:
        return None

    # Use Path.name to get only the filename part (strips directories)
    safe_name = Path(str(filename)).name
    if not safe_name or safe_name in (".", "..", ""):
        return None

    custom_dir = Path(custom_dir_str).resolve()
    target_path = (custom_dir / safe_name).resolve()

    if is_within_directory(custom_dir, target_path):
        return str(target_path)

    return None


def get_builtin_test_class_names():
    """
    Return a set of all built-in test class names.
    Used to prevent custom templates from overriding built-ins.
    """
    builtin_names = set()
    try:
        for resource in importlib.resources.files(PACKAGE).iterdir():
            if (
                resource.suffix == ".py"
                and resource.is_file()
                and resource.name not in ["__init__.py", "base.py"]
            ):
                builtin_names.add(resource.stem)
    except Exception as e:
        logger.error(f"Error getting built-in test class names: {e}")
    return builtin_names


def get_test_class_from_file(file_path, class_name):
    """
    Dynamically load a class from a given file path.
    """
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return None

    if not os.path.isfile(file_path):
        logger.error(f"Path is not a file: {file_path}")
        return None

    if not os.access(file_path, os.R_OK):
        logger.error(f"File is not readable (Permission Denied): {file_path}")
        return None

    try:
        # Check cache first
        mtime = os.path.getmtime(file_path)
        cache_key = f"file:{file_path}:{class_name}"
        if cache_key in _test_class_load_cache:
            cached_mtime, cached_cls = _test_class_load_cache[cache_key]
            if cached_mtime == mtime:
                return cached_cls

        spec = importlib.util.spec_from_file_location(class_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            cls = getattr(module, class_name)
            # Store in cache
            _test_class_load_cache[cache_key] = (mtime, cls)
            return cls
    except Exception as e:
        logger.error(f"Failed to load class {class_name} from {file_path}: {e}")
    return None


def get_test_class_from_package(package, class_name):
    """
    Load a class from a python package.
    """
    try:
        module_name = f"{package}.{class_name}"
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except Exception as e:
        logger.error(f"Failed to load class {class_name} from package {package}: {e}")
    return None


def get_all_available_test_classes():
    """
    Return all available testcase classes from both built-in package and custom directory.
    Built-in classes take priority and cannot be overridden by custom templates.
    Returns:
        dict: { class_name: {"class": cls, "source": "built-in"|"custom", "path": path} }
    """
    test_classes = {}
    builtin_names = set()

    # 1. Load built-in testcases
    try:
        for resource in importlib.resources.files(PACKAGE).iterdir():
            if (
                resource.suffix == ".py"
                and resource.is_file()
                and resource.name not in ["__init__.py", "base.py"]
            ):
                class_name = resource.stem
                builtin_names.add(class_name)
                cls = get_test_class_from_package(PACKAGE, class_name)
                if cls:
                    test_classes[class_name] = {
                        "class": cls,
                        "source": "built-in",
                    }
    except Exception as e:
        logger.error(f"Error loading built-in testcases: {e}")

    # 2. Load custom testcases (if enabled)
    if not getattr(settings, "ENABLE_CUSTOM_TESTCASES", False):
        return test_classes

    from networktests.models import CustomTestTemplate

    enabled_templates = {
        t.class_name: t for t in CustomTestTemplate.objects.filter(is_enabled=True)
    }

    custom_dir = getattr(settings, "CUSTOM_TESTCASES_PATH", None)
    if custom_dir and os.path.exists(custom_dir):
        for filename in os.listdir(custom_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                class_name = Path(filename).stem
                # Prevent custom templates from overriding built-in classes
                if class_name in builtin_names:
                    logger.warning(
                        f"Custom template '{class_name}' ignored: "
                        "cannot override built-in test class"
                    )
                    continue
                if class_name in enabled_templates:
                    file_path = get_safe_custom_template_path(filename)
                    if not file_path:
                        continue

                    cls = get_test_class_from_file(file_path, class_name)
                    if cls and is_valid_test_class(cls):
                        test_classes[class_name] = {
                            "class": cls,
                            "source": "custom",
                            "path": file_path,
                        }
                    elif cls:
                        logger.warning(
                            f"Custom template '{class_name}' ignored: "
                            "class does not implement required test interface"
                        )

    return test_classes


def sync_custom_testcases():
    """
    Scan the custom testcases directory and update the database entries.
    Also removes database entries for files that no longer exist on disk.

    Returns:
        tuple: (count_synced, error_message)
    """
    global _test_class_load_cache
    _test_class_load_cache = {}  # Clear cache during sync

    from networktests.models import CustomTestTemplate

    custom_dir = getattr(settings, "CUSTOM_TESTCASES_PATH", None)
    if not custom_dir:
        return 0, "Custom testcases directory not configured (CUSTOM_TESTCASES_PATH)."

    if not os.path.exists(custom_dir):
        return 0, f"Custom directory does not exist: {custom_dir}"

    if not os.path.isdir(custom_dir):
        return 0, f"Custom path is not a directory: {custom_dir}"

    if not os.access(custom_dir, os.R_OK):
        return 0, f"Custom directory is not readable (Permission Denied): {custom_dir}"

    builtin_names = get_builtin_test_class_names()

    try:
        found_classes = set()
        count = 0
        skipped_builtins = []
        for filename in os.listdir(custom_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                safe_filename = sanitize_filename(filename)
                class_name = Path(safe_filename).stem

                # Skip files that would conflict with built-in test classes
                if class_name in builtin_names:
                    skipped_builtins.append(class_name)
                    logger.warning(
                        f"Skipping '{class_name}': conflicts with built-in test class"
                    )
                    continue

                # Validate the file actually contains a valid test class
                file_path = get_safe_custom_template_path(safe_filename)
                if not file_path:
                    continue

                cls = get_test_class_from_file(file_path, class_name)
                if not cls or not is_valid_test_class(cls):
                    logger.warning(
                        f"Skipping '{class_name}': invalid Python file or missing DiagNetTest interface"
                    )
                    continue

                found_classes.add(class_name)
                _, created = CustomTestTemplate.objects.update_or_create(
                    class_name=class_name,
                    defaults={
                        "file_name": safe_filename,
                        "last_seen_at": timezone.now(),
                    },
                )
                if created:
                    count += 1

        # Clean up database entries for files that no longer exist
        deleted_count, _ = CustomTestTemplate.objects.exclude(
            class_name__in=found_classes
        ).delete()
        if deleted_count > 0:
            logger.info(f"Removed {deleted_count} stale template entries from database")

        error_msg = None
        if skipped_builtins:
            error_msg = (
                f"Skipped {len(skipped_builtins)} file(s) that conflict with "
                f"built-in test classes: {', '.join(skipped_builtins)}"
            )

        return count, error_msg
    except OSError as e:
        logger.error(f"Error scanning custom directory {custom_dir}: {e}")
        return 0, f"System error scanning directory: {e}"
