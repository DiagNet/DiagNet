from django.http import JsonResponse
import importlib.resources


def get_all_testcases(request):
    testcases = {}
    package = "networktests.testcases"
    for resource in importlib.resources.files(package).iterdir():
        if (
            resource.suffix == ".py"
            and resource.is_file()
            and resource.name not in ["__init__.py", "base.py"]
        ):
            module_name = f"{package}.{resource.stem}"
            module = importlib.import_module(module_name)

            cls = getattr(module, resource.stem)
            print(cls._required_params)

            testcases[resource.stem] = cls._required_params

    return JsonResponse({"testcases": testcases})
