from datetime import timedelta
from typing import List, Optional

from django.contrib.auth.decorators import permission_required
from django.db.models import Count, Q, QuerySet
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from networktests.models import TestResult
from testgroups.models import TestGroup


def get_dashboard_data(range_code: str, group_name: Optional[str]):
    now = timezone.now()

    RANGE_OPTIONS = {
        "24h": {"delta": timedelta(hours=24), "label": "in the last 24 hours"},
        "7d": {"delta": timedelta(days=7), "label": "in the last 7 days"},
        "30d": {"delta": timedelta(days=30), "label": "in the last 30 days"},
        "all": {"delta": None, "label": "of all time"},
    }
    # The default in the dashboard_data view is '24h'. We honor that here.
    DEFAULT_RANGE_CODE = "24h"

    # If range_code is not a valid key, fall back to the default.
    if range_code not in RANGE_OPTIONS:
        range_code = DEFAULT_RANGE_CODE

    selected_option = RANGE_OPTIONS[range_code]
    range_label = selected_option["label"]
    delta = selected_option["delta"]
    since = now - delta if delta else None

    results_qs: QuerySet = TestResult.objects.select_related("test_case").order_by(
        "-started_at"
    )
    if since is not None:
        results_qs = results_qs.filter(started_at__gte=since)

    total = results_qs.count()
    passes = results_qs.filter(result=True).count()
    fails = total - passes

    recent = results_qs[:10]

    all_groups = TestGroup.objects.prefetch_related("testcases").order_by("name")
    group_results_filter = Q()
    if since:
        group_results_filter = Q(testcases__results__started_at__gte=since)

    groups_with_stats = all_groups.annotate(
        total_count=Count("testcases__results", filter=group_results_filter),
        pass_count=Count(
            "testcases__results",
            filter=group_results_filter & Q(testcases__results__result=True),
        ),
    ).filter(total_count__gt=0)

    group_labels: List[str] = [g.name for g in groups_with_stats]
    group_passes: List[int] = [g.pass_count for g in groups_with_stats]
    group_fails: List[int] = [g.total_count - g.pass_count for g in groups_with_stats]

    selected_group = None

    if group_name:
        try:
            selected_group = all_groups.get(name=group_name)
        except TestGroup.DoesNotExist:
            selected_group = None

    if not selected_group and all_groups.exists():
        selected_group = all_groups.first()

    testcase_labels: List[str] = []
    testcase_passes: List[int] = []
    testcase_fails: List[int] = []
    recent_list: List[dict] = []

    if selected_group:
        testcase_results_filter = Q()
        if since:
            testcase_results_filter = Q(results__started_at__gte=since)

        testcases_with_stats = selected_group.testcases.annotate(
            total_count=Count("results", filter=testcase_results_filter),
            pass_count=Count(
                "results",
                filter=testcase_results_filter & Q(results__result=True),
            ),
        ).order_by("label")

        testcase_labels = [tc.label for tc in testcases_with_stats]
        testcase_passes = [tc.pass_count for tc in testcases_with_stats]
        testcase_fails = [tc.total_count - tc.pass_count for tc in testcases_with_stats]

    for r in recent:
        recent_list.append(
            {
                "test_case": r.test_case.label,
                "result": r.result,
                "started_at": r.started_at,
                "log": r.log,
            }
        )

    return {
        "total": total,
        "passes": passes,
        "fails": fails,
        "recent": recent_list,
        "range_code": range_code,
        "range_label": range_label,
        "group_labels": group_labels,
        "group_passes": group_passes,
        "group_fails": group_fails,
        "selected_group": selected_group.name if selected_group else None,
        "testcase_labels": testcase_labels,
        "testcase_passes": testcase_passes,
        "testcase_fails": testcase_fails,
        "groups": [g.name for g in all_groups],
    }


@permission_required(
    [
        "networktests.view_testcase",
        "networktests.view_testresult",
        "testgroups.view_testgroup",
    ]
)
def dashboard_data(request):
    range_code = request.GET.get("range", "24h")
    group_name = request.GET.get("tcgroup", None)
    data = get_dashboard_data(range_code, group_name)

    return JsonResponse(data)


@permission_required(
    [
        "networktests.view_testcase",
        "networktests.view_testresult",
        "testgroups.view_testgroup",
    ]
)
def index(request):
    """
    Main Dashboard:
    Left:
        • TestGroup Chart (Pass/Fail)
        • TestCase Chart (Pass/Fail) for selected group
    Right:
        • KPI cards
        • Recent Test Runs table with filter
    """
    return render(request, "dashboard/dashboard.html")
