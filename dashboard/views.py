from datetime import timedelta
from typing import List, Optional

from django.db.models import QuerySet
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from networktests.models import TestResult
from testgroups.models import TestGroup


def get_dashboard_data(range_code: str, group_name: Optional[str]):
    now = timezone.now()
    since: Optional[timezone.datetime] = None
    range_label = "all results"

    if range_code == "24h":
        since = now - timedelta(hours=24)
        range_label = "last 24 hours"
    elif range_code == "7d":
        since = now - timedelta(days=7)
        range_label = "last 7 days"
    elif range_code == "30d":
        since = now - timedelta(days=30)
        range_label = "last 30 days"
    elif range_code == "all":
        since = None

    results_qs: QuerySet = TestResult.objects.select_related("test_case").order_by(
        "-started_at"
    )
    if since is not None:
        results_qs = results_qs.filter(started_at__gte=since)

    total = results_qs.count()
    passes = results_qs.filter(result=True).count()
    fails = results_qs.filter(result=False).count()

    recent = results_qs[:10]

    groups = TestGroup.objects.prefetch_related("testcases").order_by("name")

    group_labels: List[str] = []
    group_passes: List[int] = []
    group_fails: List[int] = []

    for group in groups:
        # fetch testcase ids once
        case_ids = list(group.testcases.values_list("id", flat=True))
        if not case_ids:
            continue

        group_total = results_qs.filter(test_case_id__in=case_ids).count()
        if group_total == 0:
            continue

        group_pass_count = results_qs.filter(
            test_case_id__in=case_ids, result=True
        ).count()
        group_fail_count = group_total - group_pass_count

        group_labels.append(group.name)
        group_passes.append(group_pass_count)
        group_fails.append(group_fail_count)

    selected_group = None

    if group_name:
        try:
            selected_group = TestGroup.objects.get(name=group_name)
        except TestGroup.DoesNotExist:
            selected_group = None

    if not selected_group and groups.exists():
        selected_group = groups.first()

    testcase_labels: List[str] = []
    testcase_passes: List[int] = []
    testcase_fails: List[int] = []

    if selected_group:
        for case in selected_group.testcases.all():
            case_total = results_qs.filter(test_case_id=case.id).count()
            case_pass = results_qs.filter(test_case_id=case.id, result=True).count()
            case_fail = case_total - case_pass

            testcase_labels.append(case.label)
            testcase_passes.append(case_pass)
            testcase_fails.append(case_fail)

        recent_list = []

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
        "groups": [g.name for g in groups],
    }


def dashboard_data(request):
    range_code = request.GET.get("range", "24h")
    group_name = request.GET.get("tcgroup", None)
    data = get_dashboard_data(range_code, group_name)

    return JsonResponse(data)


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
