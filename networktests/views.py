import importlib.resources
import json
from io import BytesIO

from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, QuerySet
from django.http import (
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.decorators.http import require_http_methods
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from devices.models import Device

from .models import TestCase, TestDevice, TestParameter

package = "networktests.testcases"


def index(request):
    return render(request, "networktests/index.html")


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


def get_class_reference_for_test_class_string(test_class):
    """
    Dynamically import and return a test class by its name.

    Args:
        test_class (str): Name of the test class.

    Returns:
        type: The class reference corresponding to the given test class name.

    Raises:
        ImportError: If the module cannot be imported. (see importlib.import_module())
        AttributeError: If the class is not found inside the imported module. (see importlib.import_module())
    """
    module_name = f"{package}.{test_class}"
    module = importlib.import_module(module_name)
    cls = getattr(module, test_class)
    return cls


def create_test(request):
    """
    Handle POST requests to create a new test case with its parameters.

    Args:
        request (HttpRequest): Incoming HTTP request containing JSON data with:
            - test_class (str): Name of the test class/module.
            - required_parameters (dict, optional): Required parameters for the test.
            - optional_parameters (dict, optional): Optional parameters for the test.

    Returns:
        JsonResponse: Status message indicating success or fail.

    Expected JSON structure:
        {
            "test_class": "ExampleTest",
            "required_parameters": {"param1": "value1"},
            "optional_parameters": {"param2": "value2"}
        }
    """
    if request.method != "POST":
        return JsonResponse({"status": "fail", "message": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "fail", "message": "Invalid JSON"}, status=400)

    test_class: str = data.get("test_class")
    required_params = data.get("required_parameters", {})
    optional_params = data.get("optional_parameters", {})
    device_params = data.get("device_parameters", {})
    label = data.get("label", {})
    expected_result = data.get("expected_result", {})

    # Check if parsed parameters are valid
    class_reference = get_class_reference_for_test_class_string(test_class)
    parseable_parameters = {**required_params, **optional_params}

    try:
        class_reference().check_parameter_validity(**parseable_parameters)
    except Exception as e:
        return JsonResponse({"status": "fail", "message": str(e)}, status=500)

    try:
        new_test = TestCase()
        new_test.test_module = test_class
        new_test.expected_result = expected_result
        new_test.label = label
        new_test.save()
    except Exception as e:
        return JsonResponse({"status": "fail", "message": str(e)}, status=500)

    for param, value in {**required_params, **optional_params}.items():
        try:
            if param in device_params:
                new_param = TestDevice()
                new_param.device = Device.objects.get(name=value)
            else:
                new_param = TestParameter()
                new_param.value = value

            new_param.name = param
            new_param.test_case = new_test
            new_param.save()
        except Exception as e:
            return JsonResponse({"status": "fail", "message": str(e)}, status=500)

    return JsonResponse({"status": "success"}, status=201)


def get_parameters_of_specific_testcase(request):
    """
    Retrieve the parameter specifications for a given test case class.

    Args:
        request (HttpRequest): Django request object with a GET parameter:
            - test_class (str, optional): Name of the test class to query. Defaults to "".

    Returns:
        JsonResponse: A JSON object containing:
            - required (list[str]): List of required parameters, with type appended if missing.
            - optional (list[str]): List of optional parameters, with type appended if missing.
            - mul_exclusive (list[str]): List of mutually exclusive parameters defined in the class.
    """
    test_name = request.GET.get("test_class", "")
    cls = get_class_reference_for_test_class_string(test_name)

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


def get_all_available_testcases(request):
    """
    Scan the testcases package and list all available test case classes.

    Returns:
        list[str]: A list of class names corresponding to Python files in the package.
    """
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

    return JsonResponse({"results": testcases})


def get_doc_of_testcase(request):
    """
    Return a JSON response with the documentation for a specific test case.

    Args:
        request (HttpRequest): Django request object with a GET parameter:
            - test_class (str, optional): Name of the test class to query. Defaults to "".

    Returns:
        JsonResponse: A JSON object containing:
            - docstring (str): The docstring of the given test_class
    """

    return JsonResponse({"results": "work in progress"})


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
    # context = {"title": "test", "msg": "hello bro"}
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

def generate_report(request):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Testbericht", styles["Heading1"]))
    elements.append(Spacer(1, 12))

    testcases = TestCase.objects.all()

    if not testcases:
        elements.append(Paragraph("Keine Testfälle vorhanden.", styles["Normal"]))
    else:
        data = [["Label", "Modul", "Erwartetes Ergebnis", "Letztes Ergebnis", "Datum"]]

        for tc in testcases:
            latest_result = tc.results.order_by('-finished_at').first()

            data.append([
                tc.label,
                tc.test_module,
                "PASS" if tc.expected_result else "FAIL",
                "PASS" if (latest_result and latest_result.result) else "FAIL",
                latest_result.finished_at.strftime("%d.%m.%Y %H:%M") if latest_result and latest_result.finished_at else "-"
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(table)

    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=test_report.pdf"
    return response