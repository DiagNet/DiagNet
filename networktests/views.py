import importlib.resources
import json
import logging
from datetime import date
from io import BytesIO

from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, QuerySet
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.decorators.http import require_http_methods

from devices.models import Device
from networktests.models import TestCase

from .models import TestDevice, TestParameter
from .pdf_report import PDFReport

logger = logging.getLogger(__name__)


package = "networktests.testcases"


def index(request):
    return render(request, "networktests/index.html")


def get_all_testcases(request):
    """
    Return available testcase classes and their parameter specs.
    """
    testcases = {}
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


def get_class_reference_for_test_class_string(test_class):
    """
    Import and return the test class by name.
    """
    module_name = f"{package}.{test_class}"
    module = importlib.import_module(module_name)
    cls = getattr(module, test_class)
    return cls


def store_test_parameter(parent, parameter, value):
    """
    Stores test parameters into the database.
    Also covers recursive parameter referencing

    Args:
        parent: The Parent Table of the given parameters, either a test case or another parameter.
        parameter: The name of the parameter that gets stored.
        value: The value of the parameter that gets stored.

    Returns:
        JsonResponse: Returned only when a mistake happens, otherwise nothing is returned.
    """
    try:
        if not isinstance(value, list) and value["isDevice"]:
            new_param = TestDevice()
            new_param.device = Device.objects.get(id=value["value"])
        else:
            new_param = TestParameter()
            if isinstance(value, list):
                new_param.value = "list"
                new_param.save()
                for i, child_parameters in enumerate(value):
                    list_item = TestParameter()
                    list_item.name = f"list-item-{i}"
                    list_item.value = ""
                    list_item.parent_test_parameter = new_param
                    list_item.save()

                    for param, value in child_parameters.items():
                        out = store_test_parameter(list_item, param, value)
                        if out:
                            return out
            else:
                new_param.value = value["value"]

        new_param.name = parameter
        if isinstance(parent, TestCase):
            new_param.test_case = parent
        elif isinstance(parent, TestParameter):
            new_param.parent_test_parameter = parent

        new_param.save()
    except Exception as e:
        return JsonResponse({"status": "fail", "message": str(e)}, status=500)


def create_test(request):
    """
    Handle POST requests to create a new test case with its parameters.

    Args:
        request (HttpRequest): Incoming HTTP request containing JSON data with:
            - test_class (str): Name of the test class/module.
            - parameters (dict, optional): General parameters for the test.
            - label (str, optional): A descriptive label for the test case.
            - description (str, optional): A textual description of what the test case does.
            - expected_result (bool, optional): Expected result of the test (True for PASS, False for FAIL).

    Returns:
        JsonResponse: Status message indicating success or failure.

    Expected JSON structure:
        {
            "test_class": "ExampleTest",
            "parameters": {"param1": "value1"},
            "label": "My Testcase",
            "description": "Checks routing table correctness",
            "expected_result": true
        }
    """

    if request.method != "POST":
        return JsonResponse({"status": "fail", "message": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "fail", "message": "Invalid JSON"}, status=400)

    test_class: str = data.get("test_class")
    params = data.get("parameters", {})
    label = data.get("label", {})
    description = data.get("description", {})
    expected_result = data.get("expected_result", {})

    class_reference = get_class_reference_for_test_class_string(test_class)

    try:
        class_reference().check_parameter_validity(**params)
    except Exception as e:
        return JsonResponse({"status": "fail", "message": str(e)}, status=500)

    try:
        new_test = TestCase()
        new_test.test_module = test_class
        new_test.expected_result = expected_result
        new_test.label = label
        new_test.description = description
        new_test.save()
    except Exception as e:
        return JsonResponse({"status": "fail", "message": str(e)}, status=500)

    for param, value in params.items():
        out = store_test_parameter(new_test, param, value)
        if out:
            return out

    return JsonResponse({"status": "success"}, status=201)


def get_parameters_of_specific_testcase(request):
    """
    Retrieve the parameter specifications for a given test case class.

    Args:
        request (HttpRequest): Django request object with a GET parameter:
            - test_class (str, optional): Name of the test class to query. Defaults to "".

    Returns:
        JsonResponse: A JSON object containing:
            - parameters (list[str]): List of parameters.
            - mul_exclusive (list[str]): List of mutually exclusive parameters defined in the class.
    """
    try:
        test_name = request.GET.get("test_class", "")
        cls = get_class_reference_for_test_class_string(test_name)

        return JsonResponse(
            {
                "status": "SUCCESS",
                "parameters": cls._params,
                "mul_exclusive": cls._mutually_exclusive_parameters,
            }
        )
    except Exception:
        return JsonResponse(
            {
                "status": "FAIL",
                "message": "Testcase does not exist",
                "parameters": [],
                "mul_exclusive": [],
            }
        )


def get_all_available_testcases(request):
    """
    List available test case class names.
    """
    testcases = []
    for resource in importlib.resources.files(package).iterdir():
        if (
            resource.suffix == ".py"
            and resource.is_file()
            and resource.name not in ["__init__.py", "base.py"]
        ):
            class_name = resource.stem
            testcases.append(class_name)

    return JsonResponse({"results": testcases})


def get_doc_of_testcase(request):
    """
    Return doc info for a test case (WIP).
    """
    try:
        cls = get_class_reference_for_test_class_string(request.GET.get("name", ""))
    except (ImportError, AttributeError):
        return JsonResponse(
            {"status": "fail", "message": "Testcase does not exist"}, status=500
        )

    return JsonResponse({"status": "success", "results": cls.__doc__ or ""})


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


def create_test_page(request):
    return render(request, "networktests/partials/create_popup/create_test_popup.html")


class TestCaseListView(generic.ListView):
    model = TestCase
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        if hasattr(self, "queryset") and self.queryset is not None:
            return self.queryset
        return super().get_queryset()


@require_http_methods(["GET"])
def run_testcase(request, pk):
    testcase = get_object_or_404(TestCase, pk=pk)
    _ = testcase.run()
    return redirect("networktests-page")


@require_http_methods(["DELETE"])
def delete_testcase(request, pk):
    testcase = get_object_or_404(TestCase, pk=pk)
    testcase.delete()
    return HttpResponse(status=200)


@permission_required(
    [
        "networktests.view_testcase",
        "networktests.view_testresult",
        "testgroups.view_testgroup",
    ]
)
def export_report_pdf(request):
    buffer = BytesIO()
    report = PDFReport(buffer)
    report.generate()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    datestamp = date.today().strftime("%Y-%m-%d")
    filename = f"DiagNet-Report-{datestamp}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
