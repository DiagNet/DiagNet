from django.http import JsonResponse
import importlib.resources


def get_all_testcases(request):
    files = []
    package = "networktests.testcases"
    for resource in importlib.resources.files(package).iterdir():
        if (
            resource.suffix == ".py"
            and resource.is_file()
            and resource.name not in ["__init__.py", "base.py"]
        ):
            files.append(resource.name.replace(".py", ""))
    return JsonResponse({"testcases": files})
