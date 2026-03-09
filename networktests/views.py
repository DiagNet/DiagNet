import json
import logging
from datetime import date
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, QuerySet
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views import generic
from django.views.decorators.http import require_http_methods, require_POST

from devices.models import Device
from networktests.forms import TestGroupForm
from networktests.models import (
    CustomTestTemplate,
    TestCase,
    TestDevice,
    TestGroup,
    TestParameter,
    TestResult,
)
from networktests.pdf_report import PDFReport
from networktests.testcases.base import get_parameter_names
from networktests.utils import (
    get_all_available_test_classes,
    sync_custom_testcases,
)

logger = logging.getLogger(__name__)


@permission_required("networktests.view_testcase", raise_exception=True)
def index(request):
    return render(request, "networktests/index.html")


@permission_required("networktests.view_testcase", raise_exception=True)
def get_all_testcases(request):
    """
    Return available testcase classes and their parameter specs.
    """
    testcases = {}
    available_classes = get_all_available_test_classes()

    for class_name, info in available_classes.items():
        cls = info["class"]

        # Extract parameter names from the class definition
        required_params_raw = cls._get_required_params()
        optional_params_raw = cls._get_optional_params()

        required_params, optional_params = get_parameter_names(
            required_params_raw, optional_params_raw
        )

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
    available_classes = get_all_available_test_classes()
    if test_class in available_classes:
        return available_classes[test_class]["class"]
    raise ImportError(f"Test class {test_class} not found")


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


@permission_required("networktests.add_testcase", raise_exception=True)
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


@permission_required("networktests.view_testcase", raise_exception=True)
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


@permission_required("networktests.view_testcase", raise_exception=True)
def get_all_available_testcases(request):
    """
    List available test case class names with their source information.
    """
    available_classes = get_all_available_test_classes()
    results = [
        {"name": name, "source": info["source"]}
        for name, info in available_classes.items()
    ]
    return JsonResponse({"results": results})


@permission_required("networktests.view_testcase", raise_exception=True)
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


@permission_required("networktests.view_testcase", raise_exception=True)
def test_list(request):
    return render(request, "networktests/testcases_list.html")


@permission_required("networktests.view_testcase", raise_exception=True)
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


@permission_required("networktests.add_testcase", raise_exception=True)
def create_test_page(request):
    return render(request, "networktests/partials/create_popup/create_test_popup.html")


class TestCaseListView(PermissionRequiredMixin, generic.ListView):
    permission_required = "networktests.view_testcase"
    model = TestCase
    paginate_by = 25

    def get_queryset(self) -> QuerySet:
        if hasattr(self, "queryset") and self.queryset is not None:
            return self.queryset
        return super().get_queryset()


@require_POST
@permission_required("networktests.add_testresult", raise_exception=True)
def run_testcase(request, pk):
    testcase = get_object_or_404(TestCase, pk=pk)
    try:
        testcase.run()
        msg = f"Successfully executed test: {testcase.label}"
        level = "success"
    except Exception as e:
        logger.exception("Error running testcase %s", testcase.label)
        msg = f"Failed to run test {testcase.label}: {e}"
        level = "danger"

    if request.headers.get("HX-Request"):
        testcase.refresh_from_db()
        testcase = TestCase.objects.prefetch_related("results").get(pk=pk)
        response = render(
            request,
            "networktests/partials/testcase_row.html",
            {"testcase": testcase},
        )
        response["HX-Trigger"] = json.dumps(
            {"showMessage": {"message": msg, "level": level}}
        )
        return response

    if level == "success":
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect("networktests-page")


@require_http_methods(["DELETE"])
@permission_required("networktests.delete_testcase", raise_exception=True)
def delete_testcase(request, pk):
    testcase = get_object_or_404(TestCase, pk=pk)
    testcase.delete()
    return HttpResponse(status=200)


@permission_required(
    [
        "networktests.view_testcase",
        "networktests.view_testresult",
        "networktests.view_testgroup",
    ],
    raise_exception=True,
)
@require_http_methods(["GET"])
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


@require_http_methods(["GET"])
@permission_required("networktests.view_testcase", raise_exception=True)
def testcase_detail_view(request, pk):
    testcase = get_object_or_404(
        TestCase.objects.prefetch_related(
            "parameters",
            Prefetch(
                "devices",
                queryset=TestDevice.objects.select_related("device"),
            ),
            Prefetch(
                "results",
                queryset=TestResult.objects.order_by("-attempt_id"),
            ),
        ),
        pk=pk,
    )
    results_list = testcase.results.all()

    paginator = Paginator(results_list, 10)
    page_number = request.GET.get("page", 1)
    results_page = paginator.get_page(page_number)

    context = {
        "testcase": testcase,
        "results_page": results_page,
    }

    if request.headers.get("HX-Target") == f"history-card-{pk}":
        return render(request, "networktests/partials/history_card.html", context)

    return render(request, "networktests/partials/testcase_details.html", context)


@login_required
@permission_required("networktests.change_customtesttemplate", raise_exception=True)
def manage_custom_templates(request):
    """
    View to list and manage custom test templates.
    """
    templates = CustomTestTemplate.objects.all().order_by("class_name")
    return render(
        request,
        "networktests/manage_templates.html",
        {
            "templates": templates,
            "feature_enabled": getattr(settings, "ENABLE_CUSTOM_TESTCASES", False),
        },
    )


@require_http_methods(["POST"])
@login_required
@permission_required("networktests.change_customtesttemplate", raise_exception=True)
def toggle_custom_template(request, pk):
    """
    Toggle the is_enabled status of a custom test template.
    """
    template = get_object_or_404(CustomTestTemplate, pk=pk)
    template.is_enabled = not template.is_enabled
    template.save()

    status = "enabled" if template.is_enabled else "disabled"
    message = f"Template '{template.class_name}' has been {status}."

    if request.headers.get("HX-Request"):
        templates = CustomTestTemplate.objects.all().order_by("class_name")
        response = render(
            request,
            "networktests/partials/templates_table.html",
            {"templates": templates},
        )
        response["HX-Trigger"] = json.dumps(
            {"showMessage": {"message": message, "level": "success"}}
        )
        return response

    messages.success(request, message)
    return redirect("manage-custom-templates")


@require_http_methods(["POST"])
@login_required
@permission_required("networktests.change_customtesttemplate", raise_exception=True)
def sync_custom_templates_view(request):
    """
    Trigger a sync of custom test templates from the file system.
    """
    count, error = sync_custom_testcases()

    if request.headers.get("HX-Request"):
        templates = CustomTestTemplate.objects.all().order_by("class_name")
        response = render(
            request,
            "networktests/partials/templates_table.html",
            {"templates": templates},
        )
        if error:
            message = f"Sync completed with warnings: {error}"
            level = "warning"
        else:
            message = f"Sync complete. Discovered {count} new template(s)."
            level = "success"

        response["HX-Trigger"] = json.dumps(
            {"showMessage": {"message": message, "level": level}}
        )
        return response

    if error:
        messages.warning(request, f"Sync completed with warnings: {error}")
    else:
        messages.success(request, f"Sync complete. Discovered {count} new template(s).")
    return redirect("manage-custom-templates")


@require_http_methods(["GET"])
def testgroup_form_modal(request, pk=None):
    """
    Return the testgroup create/edit modal HTML via HTMX.
    Reuses the same form and template for both create and edit.
    """
    if pk:
        if not request.user.has_perm("networktests.change_testgroup"):
            raise PermissionDenied
        group = get_object_or_404(TestGroup, pk=pk)
        form = TestGroupForm(instance=group)
    else:
        if not request.user.has_perm("networktests.add_testgroup"):
            raise PermissionDenied
        group = None
        form = TestGroupForm()

    return render(
        request,
        "networktests/partials/testgroup_modal.html",
        {"form": form, "group": group},
    )


@require_http_methods(["POST"])
def save_testgroup(request, pk=None):
    """
    Handle POST for creating or updating a TestGroup.
    Returns an HTMX trigger to refresh the dashboard.
    """
    if pk:
        if not request.user.has_perm("networktests.change_testgroup"):
            return HttpResponse(status=403)
        group = get_object_or_404(TestGroup, pk=pk)
        form = TestGroupForm(request.POST, instance=group)
        action = "updated"
    else:
        if not request.user.has_perm("networktests.add_testgroup"):
            return HttpResponse(status=403)
        form = TestGroupForm(request.POST)
        action = "created"

    if form.is_valid():
        saved_group = form.save()
        msg = f"Test group '{form.cleaned_data['name']}' {action}."

        if pk:
            # Edit: swap just this accordion item (kept open), no full refresh
            saved_group = TestGroup.objects.prefetch_related(
                Prefetch(
                    "testcases",
                    queryset=TestCase.objects.prefetch_related("results").order_by(
                        "label"
                    ),
                )
            ).get(pk=pk)
            response = render(
                request,
                "networktests/partials/group_accordion_item.html",
                {"group": saved_group, "accordion_open": True},
            )
            response["HX-Retarget"] = f"#accordion-item-group-{pk}"
            response["HX-Reswap"] = "outerHTML"
        else:
            # Create: need full dashboard refresh to insert new accordion
            response = HttpResponse(status=204)

        triggers = {
            "closeModal": True,
            "showMessage": {"message": msg, "level": "success"},
        }
        if not pk:
            triggers["refreshDashboard"] = True
        response["HX-Trigger"] = json.dumps(triggers)
        return response

    return render(
        request,
        "networktests/partials/testgroup_form.html",
        {"form": form, "group": group if pk else None},
    )


@permission_required("networktests.delete_testgroup", raise_exception=True)
@require_http_methods(["POST"])
def delete_testgroup(request, pk):
    """Delete a TestGroup and refresh the dashboard."""
    group = get_object_or_404(TestGroup, pk=pk)
    name = group.name
    group.delete()
    response = HttpResponse(status=204)
    response["HX-Trigger"] = json.dumps(
        {
            "refreshDashboard": True,
            "showMessage": {
                "message": f"Test group '{name}' deleted.",
                "level": "success",
            },
        }
    )
    return response


@permission_required(
    ["networktests.view_testcase", "networktests.view_testgroup"],
    raise_exception=True,
)
@require_http_methods(["POST"])
def run_group_tests(request, pk):
    """
    Run all tests belonging to a TestGroup sequentially.
    Returns the updated testcases table for this group.
    """
    group = get_object_or_404(TestGroup, pk=pk)
    testcases = list(group.testcases.prefetch_related("results").order_by("label"))

    passed = 0
    failed = 0
    for tc in testcases:
        try:
            tc.run()
            passed += 1
        except Exception:
            logger.exception(
                "Error running testcase %s in group %s", tc.label, group.name
            )
            failed += 1

    msg = f"Group '{group.name}': {passed} passed, {failed} failed."
    level = "success" if failed == 0 else "warning"

    # Re-fetch to get updated results
    group.refresh_from_db()
    updated_testcases = group.testcases.prefetch_related("results").order_by("label")

    paginator = Paginator(updated_testcases, 25)
    page_obj = paginator.get_page(request.POST.get("page") or request.GET.get("page"))

    response = render(
        request,
        "networktests/partials/group_testcases_table.html",
        {"testcases": page_obj, "page_obj": page_obj, "group": group},
    )
    response["HX-Trigger"] = json.dumps(
        {"showMessage": {"message": msg, "level": level}}
    )
    return response


@permission_required(
    [
        "networktests.view_testcase",
        "networktests.view_testresult",
        "networktests.view_testgroup",
    ],
    raise_exception=True,
)
@require_http_methods(["GET"])
def export_group_pdf(request, pk):
    """Generate a PDF report filtered to a specific TestGroup."""
    group = get_object_or_404(TestGroup, pk=pk)
    buffer = BytesIO()
    report = PDFReport(buffer, group=group)
    report.generate()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    datestamp = date.today().strftime("%Y-%m-%d")
    filename = f"DiagNet-Report-{slugify(group.name)}-{datestamp}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@permission_required(
    ["networktests.view_testcase", "networktests.view_testgroup"],
    raise_exception=True,
)
@require_http_methods(["GET"])
def dashboard_content(request):
    """
    HTMX partial: renders the accordion dashboard with all groups + all-tests section.
    """
    testgroups = TestGroup.objects.prefetch_related(
        Prefetch(
            "testcases",
            queryset=TestCase.objects.prefetch_related("results").order_by("label"),
        )
    ).order_by("name")
    all_testcases = TestCase.objects.prefetch_related("results").order_by("label")

    return render(
        request,
        "networktests/partials/dashboard_content.html",
        {"testgroups": testgroups, "all_testcases": all_testcases},
    )


@permission_required(
    ["networktests.view_testcase", "networktests.view_testgroup"],
    raise_exception=True,
)
@require_http_methods(["GET"])
def group_table_partial(request, pk):
    """HTMX partial: returns just the testcases table for a specific group."""
    group = get_object_or_404(TestGroup, pk=pk)
    testcases_qs = group.testcases.prefetch_related("results").order_by("label")
    paginator = Paginator(testcases_qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "networktests/partials/group_testcases_table.html",
        {"testcases": page_obj, "page_obj": page_obj, "group": group},
    )


@permission_required("networktests.view_testcase", raise_exception=True)
@require_http_methods(["GET"])
def all_tests_table_partial(request):
    """HTMX partial: returns the testcases table for 'All Tests'."""
    all_testcases = TestCase.objects.prefetch_related("results").order_by("label")
    paginator = Paginator(all_testcases, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "networktests/partials/group_testcases_table.html",
        {"testcases": page_obj, "page_obj": page_obj},
    )


@permission_required(
    ["networktests.view_testcase", "networktests.view_testgroup"],
    raise_exception=True,
)
@require_http_methods(["GET"])
def group_accordion_item_partial(request, pk):
    """HTMX partial: returns a single accordion item for a group, kept open."""
    group = get_object_or_404(
        TestGroup.objects.prefetch_related(
            Prefetch(
                "testcases",
                queryset=TestCase.objects.prefetch_related("results").order_by("label"),
            )
        ),
        pk=pk,
    )
    return render(
        request,
        "networktests/partials/group_accordion_item.html",
        {"group": group, "accordion_open": True},
    )
