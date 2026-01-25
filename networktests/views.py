import importlib.resources
import json
import logging

from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, QuerySet
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.decorators.http import require_http_methods
from devices.models import Device
from .models import TestDevice, TestParameter
from networktests.models import TestCase, TestResult
from testgroups.models import TestGroup

logger = logging.getLogger(__name__)


package = "networktests.testcases"


def extract_message(obj):
    """
    Find the first non-empty 'message' string inside dicts/lists
    """
    if isinstance(obj, dict):
        msg = obj.get("message")
        if isinstance(msg, str) and msg:
            return msg
        for v in obj.values():
            found = extract_message(v)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = extract_message(item)
            if found:
                return found
    return None


def format_message_for_pdf(raw, max_len=60):
    """
    Normalize logs for PDF: parse JSON and extract message
    """
    msg = None
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            msg = extract_message(parsed)
        except (json.JSONDecodeError, TypeError):
            pass

    if msg is None and isinstance(raw, (dict, list)):
        msg = extract_message(raw)

    if not msg:
        msg = str(raw) if raw else "(no message)"

    msg = msg.replace("\n", " ").replace("\r", " ")
    if len(msg) > max_len:
        msg = msg[: max_len - 3] + "..."
    return msg


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


def export_report_pdf(request):
    import io
    from django.utils import timezone
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics import renderPDF
    from reportlab.lib.utils import ImageReader

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4

    now = timezone.now()

    results = TestResult.objects.select_related("test_case").order_by("-started_at")[
        :50
    ]

    groups = TestGroup.objects.all().prefetch_related("testcases")

    group_labels_all: list[str] = []
    group_passes_all: list[int] = []
    group_fails_all: list[int] = []

    for g in groups:
        tcs = g.testcases.all()
        p = TestResult.objects.filter(test_case__in=tcs, result=True).count()
        f = TestResult.objects.filter(test_case__in=tcs, result=False).count()

        if p == 0 and f == 0:
            continue

        group_labels_all.append(g.name)
        group_passes_all.append(p)
        group_fails_all.append(f)

    group_chart_chunks = [
        (
            group_labels_all[i : i + 5],
            group_passes_all[i : i + 5],
            group_fails_all[i : i + 5],
        )
        for i in range(0, len(group_labels_all), 5)
    ]

    total_pass = sum(group_passes_all)
    total_fail = sum(group_fails_all)
    total_tests = total_pass + total_fail

    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawString(50, H - 90, "DiagNet Test Report")
    pdf.setFont("Helvetica", 16)
    pdf.setFillColor(colors.grey)
    pdf.drawString(50, H - 125, "Automated Network Test Summary")
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, H - 160, f"Generated: {now.strftime('%Y-%m-%d %H:%M')}")

    try:
        logo = ImageReader("static/images/diagnet_logo.png")
        pdf.drawImage(logo, W - 180, H - 170, width=130, preserveAspectRatio=True)
    except Exception:
        logger.debug("diagnet logo not found or could not be loaded")

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, H - 210, "Overview")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(70, H - 240, f"• Total Test Runs: {total_tests}")
    pdf.drawString(70, H - 260, f"• Passed: {total_pass}")
    pdf.drawString(70, H - 280, f"• Failed: {total_fail}")
    pdf.drawString(70, H - 300, f"• TestGroups: {len(group_labels_all)}")
    pdf.line(50, H - 320, W - 50, H - 320)
    pdf.showPage()

    for idx, (labels, passes, fails) in enumerate(group_chart_chunks, start=1):
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(50, H - 60, f"TestGroups – Pass/Fail (Block {idx})")

        drawing = Drawing(500, 280)
        bc = VerticalBarChart()
        bc.x = 40
        bc.y = 50
        bc.width = 420
        bc.height = 200

        bc.data = [passes, fails]
        bc.categoryAxis.categoryNames = labels
        bc.bars[0].fillColor = colors.HexColor("#16a34a")
        bc.bars[1].fillColor = colors.HexColor("#dc2626")
        bc.groupSpacing = 12
        bc.barSpacing = 2
        bc.valueAxis.valueMin = 0
        max_val = max(passes + fails) if (passes + fails) else 1
        bc.valueAxis.valueMax = max_val + 1
        bc.valueAxis.valueStep = max(1, max_val // 4 or 1)

        drawing.add(bc)
        renderPDF.draw(drawing, pdf, 50, H - 360)

        pdf.setFont("Helvetica", 11)
        pdf.setFillColor(colors.HexColor("#16a34a"))
        pdf.rect(60, H - 390, 10, 10, fill=True)
        pdf.setFillColor(colors.black)
        pdf.drawString(75, H - 388, "Pass")
        pdf.setFillColor(colors.HexColor("#dc2626"))
        pdf.rect(130, H - 390, 10, 10, fill=True)
        pdf.setFillColor(colors.black)
        pdf.drawString(145, H - 388, "Fail")
        pdf.showPage()

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(50, H - 60, "Group Summary")
    y = H - 110
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Group")
    pdf.drawString(250, y, "Pass")
    pdf.drawString(320, y, "Fail")
    pdf.drawString(380, y, "Total")
    pdf.line(50, y - 4, W - 50, y - 4)
    y -= 24
    pdf.setFont("Helvetica", 12)

    for name, p, f in zip(group_labels_all, group_passes_all, group_fails_all):
        if y < 70:
            pdf.showPage()
            y = H - 80
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(50, y, "Group")
            pdf.drawString(250, y, "Pass")
            pdf.drawString(320, y, "Fail")
            pdf.drawString(380, y, "Total")
            pdf.line(50, y - 4, W - 50, y - 4)
            y -= 24
            pdf.setFont("Helvetica", 12)

        pdf.drawString(50, y, name[:28])
        pdf.setFillColor(colors.HexColor("#16a34a"))
        pdf.drawRightString(290, y, str(p))
        pdf.setFillColor(colors.HexColor("#dc2626"))
        pdf.drawRightString(350, y, str(f))
        pdf.setFillColor(colors.black)
        pdf.drawRightString(420, y, str(p + f))
        y -= 20

    pdf.showPage()

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(50, H - 60, "Recent Logs – error messages")
    y = H - 110

    def draw_logs_header():
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(50, y, "Timestamp")
        pdf.drawString(160, y, "TestCase")
        pdf.drawString(310, y, "Result")
        pdf.drawString(370, y, "Message")
        pdf.line(50, y - 4, W - 50, y - 4)

    draw_logs_header()
    y -= 25
    pdf.setFont("Helvetica", 10)

    for r in results:
        if y < 70:
            pdf.showPage()
            y = H - 110
            draw_logs_header()
            y -= 25
            pdf.setFont("Helvetica", 10)

        ts = r.started_at.strftime("%Y-%m-%d %H:%M")
        tc = (r.test_case.label or "")[:24]
        raw = r.log
        msg = format_message_for_pdf(raw)

        pdf.drawString(50, y, ts)
        pdf.drawString(160, y, tc)

        if r.result:
            pdf.setFillColor(colors.HexColor("#16a34a"))
            pdf.drawString(310, y, "PASS")
        else:
            pdf.setFillColor(colors.HexColor("#dc2626"))
            pdf.drawString(310, y, "FAIL")
        pdf.setFillColor(colors.black)
        pdf.drawString(370, y, msg)
        y -= 20

    pdf.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type="application/pdf")
