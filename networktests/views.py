from django.http import JsonResponse
import importlib.resources
from django.shortcuts import render


def get_all_testcases(request):
    """
    Fetches all possible testcases, their parameters including datatypes.
    """
    testcases = {}
    package = "networktests.testcases"
    for resource in importlib.resources.files(package).iterdir():
        if (
            resource.suffix == ".py"
            and resource.is_file()
            and resource.name not in ["__init__.py", "base.py"]
        ):
            class_name = resource.stem
            module_name = f"{package}.{class_name}"
            module = importlib.import_module(module_name)

            cls = getattr(module, class_name)
            required_params = cls._required_params
            optional_params = cls._optional_params


            for i, param in enumerate(required_params):
                if ":" not in param:
                   required_params[i] = param + ":str"

            for i, param in enumerate(optional_params):
                if ":" not in param:
                   optional_params[i] = param + ":str"

            testcases[class_name] = {"required": required_params, "optional": optional_params, "mut_exclusive": cls._mutually_exclusive_parameters}

    return JsonResponse({"testcases": testcases})

def show_all_testcases(request):

    pass



def test_page(request):
    context = {"title": "test", "msg": "hello bro"}
    return render(request, "test.html", context)
