from django.core.paginator import Paginator
from django.db.models import Prefetch, Count
import json

from django.http import JsonResponse
import importlib.resources
from django.shortcuts import render

from .models import TestCase, TestParameter, TestDevice

package = "networktests.testcases"


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

            testcases[class_name] = {
                "required": required_params,
                "optional": optional_params,
                "mut_exclusive": cls._mutually_exclusive_parameters,
            }

    return JsonResponse({"testcases": testcases})


def create_test(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )

        test_class = data.get("test")
        required_params = data.get("required", {})
        optional_params = data.get("optional", {})

        try:
            new_test = TestCase()
            new_test.test_module = test_class
            new_test.expected_result = True
            new_test.label = "Work in Progress"
            new_test.save()
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

        for param, value in {**required_params, **optional_params}.items():
            try:
                new_param = TestParameter()
                new_param.name = param
                new_param.value = value
                new_param.test_case = new_test
                new_param.save()
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return JsonResponse({"status": "success", "received": data}, status=201)

        # Method not allowed
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)


def get_parameters_of_specific_testcase(request):
    test_name = request.GET.get("test_name", "")
    module_name = f"{package}.{test_name}"
    module = importlib.import_module(module_name)

    cls = getattr(module, test_name)
    required_params = cls._required_params
    optional_params = cls._optional_params

    for i, param in enumerate(required_params):
        if ":" not in param:
            required_params[i] = param + ":str"

    for i, param in enumerate(optional_params):
        if ":" not in param:
            optional_params[i] = param + ":str"

    return JsonResponse(
        {
            "required": required_params,
            "optional": optional_params,
            "mul_exclusive": cls._mutually_exclusive_parameters,
        }
    )


def search_all_available_testcases(request):
    query = request.GET.get("query", "")
    results = [item for item in global_testcases if query.lower() in str(item.lower())]
    return JsonResponse({"results": results})


def update_all_available_testcases():
    testcases = []
    package = "networktests.testcases"
    for resource in importlib.resources.files(package).iterdir():
        if (
            resource.suffix == ".py"
            and resource.is_file()
            and resource.name not in ["__init__.py", "base.py"]
        ):
            class_name = resource.stem
            testcases.append(class_name)

    return testcases


def test_list(request):
    return render(request, "networktests/testcases_list.html")


def testcases_list(request):
    qs = (
        TestCase.objects.prefetch_related(
            Prefetch("parameters", queryset=TestParameter.objects.order_by("name")),
            Prefetch(
                "devices",
                queryset=TestDevice.objects.select_related("device").order_by(
                    "device__name"
                ),
            ),
        )
        .annotate(
            num_params=Count("parameters", distinct=True),
            num_devices=Count("devices", distinct=True),
            num_results=Count("results", distinct=True),
        )
        .order_by("label")
    )

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "networktests/testcases_list.html",
        {"page_obj": page_obj, "paginator": paginator},
    )


def test_page(request):
    # context = {"title": "test", "msg": "hello bro"}
    return render(request, "create_test_popup.html")


global_testcases = update_all_available_testcases()
