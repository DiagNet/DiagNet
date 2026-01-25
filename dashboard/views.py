from typing import List, Optional

from django.shortcuts import render
from django.utils import timezone
from django.db.models import QuerySet
from datetime import timedelta

from networktests.models import TestResult
from testgroups.models import TestGroup


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

    range_code = request.GET.get("range", "24h")

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

    selected_group_name = request.GET.get("tcgroup", None)
    selected_group = None

    if selected_group_name:
        try:
            selected_group = TestGroup.objects.get(name=selected_group_name)
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

    context = {
        "total": total,
        "passes": passes,
        "fails": fails,
        "recent": recent,
        "range_code": range_code,
        "range_label": range_label,
        "group_labels": group_labels,
        "group_passes": group_passes,
        "group_fails": group_fails,
        "selected_group": selected_group,
        "testcase_labels": testcase_labels,
        "testcase_passes": testcase_passes,
        "testcase_fails": testcase_fails,
        "groups": groups,
    }

    return render(request, "dashboard/dashboard.html", context)
