import importlib.resources
import importlib.util
import os
import logging
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)

PACKAGE = "networktests.testcases"


def get_test_class_from_file(file_path, class_name):
    """
    Dynamically load a class from a given file path.
    """
    try:
        spec = importlib.util.spec_from_file_location(class_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return getattr(module, class_name)
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
    Returns:
        dict: { class_name: {"class": cls, "source": "built-in"|"custom", "path": path} }
    """
    test_classes = {}

    # 1. Load built-in testcases
    try:
        for resource in importlib.resources.files(PACKAGE).iterdir():
            if (
                resource.suffix == ".py"
                and resource.is_file()
                and resource.name not in ["__init__.py", "base.py"]
            ):
                class_name = resource.stem
                cls = get_test_class_from_package(PACKAGE, class_name)
                if cls:
                    test_classes[class_name] = {"class": cls, "source": "built-in"}
    except Exception as e:
        logger.error(f"Error loading built-in testcases: {e}")

    # 2. Load custom testcases
    custom_dir = getattr(settings, "CUSTOM_TESTCASES_DIR", None)
    if custom_dir and os.path.exists(custom_dir):
        for filename in os.listdir(custom_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                file_path = os.path.join(custom_dir, filename)
                class_name = Path(filename).stem
                cls = get_test_class_from_file(file_path, class_name)
                if cls:
                    test_classes[class_name] = {
                        "class": cls,
                        "source": "custom",
                        "path": file_path,
                    }

    return test_classes
