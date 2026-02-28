import re
from django.db.utils import IntegrityError
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import permission_required
from .models import TestGroup
from networktests.models import TestCase
from django.views.decorators.http import require_http_methods


@permission_required("testgroups.view_testgroup")
def testgroups_page(request):
    context = {}
    if len(TestGroup.objects.all()) > 0:
        context = {"testgroup_list": list(TestGroup.objects.all())}

    return render(request, "testgroup_page.html", context=context)


@permission_required("testgroups.view_testgroup")
def list_testgroups(request, error=None):
    context = {}
    if error:
        context["error"] = error

    if len(TestGroup.objects.all()) > 0:
        context["testgroup_list"] = TestGroup.objects.all()

    return render(request, "list_testgroups.html", context=context)


testgroup_name_pattern = r"[A-Za-z0-9_]+"


@permission_required("testgroups.add_testgroup")
def create_testgroup(request):
    if request.method != "POST":
        return HttpResponse("bad request method.")

    name = request.POST.get("name")

    error = None
    if not name:
        error = "name cannot be empty"
    elif not re.fullmatch(testgroup_name_pattern, name):
        error = "name can only contain letters, numbers and underscores"
    else:
        try:
            tg = TestGroup(name=name)
            tg.save()
        except IntegrityError:
            error = "a group with that name already exists."

    return list_testgroups(request, error=error)


@permission_required("testgroups.delete_testgroup")
def delete_testgroup(request):
    if request.method != "POST":
        return HttpResponse("wrong request method.")

    name = request.POST.get("name")

    try:
        TestGroup.objects.get(name=name).delete()
    except TestGroup.DoesNotExist:
        return list_testgroups(request, "a group with that name does not exist.")

    return list_testgroups(request)


@permission_required("testgroups.view_testgroup")
def get_testgroup_detail(request, name: str):
    testgroup: TestGroup
    try:
        testgroup = TestGroup.objects.get(name=name)
    except TestGroup.DoesNotExist:
        raise Http404(" This Test Group does not exist")

    context = {"testgroup": testgroup}
    return render(request, "testgroup_detail.html", context)


@permission_required("testgroups.change_testgroup")
def rename_testgroup(request, name: str):
    if request.method != "POST":
        return HttpResponse("bad request method")

    testgroup: TestGroup
    try:
        testgroup = TestGroup.objects.get(name=name)
    except TestGroup.DoesNotExist:
        raise Http404(" This Test Group does not exist")

    new_name = request.POST.get("name")

    context = {}
    error = None
    if not new_name:
        error = "name cannot be empty"
        context["error"] = error
    elif not re.fullmatch(testgroup_name_pattern, new_name):
        error = "name can only contain letters, numbers and underscores"
        context["error"] = error
    else:
        try:
            testgroup.name = new_name
            testgroup.save()
            name = new_name
        except IntegrityError:
            error = "a group with that name already exists."
            context["error"] = error

    context["name"] = name
    return render(request, "testcases_detail_title.html", context)


@permission_required("testgroups.change_testgroup")
def add_testcase_to_testgroup(request: HttpRequest):
    if request.method != "POST":
        return HttpResponseBadRequest()

    testgroup_name = request.POST.get("testgroup")
    testcase_name = request.POST.get("testcase")
    if not testgroup_name or not testcase_name:
        return HttpResponseBadRequest()

    try:
        testgroup = TestGroup.objects.get(name=testgroup_name)
        testcase = TestCase.objects.get(label=testcase_name)
    except (TestGroup.DoesNotExist, TestCase.DoesNotExist):
        return HttpResponseBadRequest("Testcase or test group does not exist")

    testgroup.testcases.add(testcase)
    return list_testcases(request, testgroup_name)


@permission_required("testgroups.change_testgroup")
def add_testcases_to_testgroup(request: HttpRequest):
    if request.method != "POST":
        return HttpResponseBadRequest()

    testgroup_pk = request.POST.get("testgroup")
    testcases = request.POST.getlist("selected_testcases")
    if not testcases or not testgroup_pk:
        return HttpResponseBadRequest("Select one or more testcases")

    try:
        testgroup = TestGroup.objects.get(pk=testgroup_pk)
    except TestGroup.DoesNotExist:
        return HttpResponseBadRequest("Test group does not exist")

    for pk in testcases:
        try:
            testcase = TestCase.objects.get(pk=pk)
        except TestCase.DoesNotExist:
            return HttpResponseBadRequest("Testcase does not exist")

        testgroup.testcases.add(testcase)

    return list_testcases(request, testgroup.name)


@permission_required("testgroups.change_testgroup")
def remove_testcase_from_testgroup(request: HttpRequest):
    if request.method != "POST":
        return HttpResponseBadRequest()

    testgroup_name = request.POST.get("testgroup")
    testcase_name = request.POST.get("testcase")
    if not testgroup_name or not testcase_name:
        return HttpResponseBadRequest()

    try:
        testgroup = TestGroup.objects.get(name=testgroup_name)
        testcase = TestCase.objects.get(label=testcase_name)
    except (TestGroup.DoesNotExist, TestCase.DoesNotExist):
        return HttpResponseBadRequest("Testcase or test group does not exist")

    testgroup.testcases.remove(testcase)
    return list_testcases(request, testgroup_name)


@permission_required("testgroups.view_testgroup")
def list_testcases(request, testgroup_name: str):
    testgroup: TestGroup
    try:
        testgroup = TestGroup.objects.get(name=testgroup_name)
    except TestGroup.DoesNotExist:
        return HttpResponseBadRequest("This Test Group does not exist")

    testcases = list(testgroup.testcases.all())

    context = {"testgroup_name": testgroup.name}
    if len(testcases) > 0:
        context["testcase_list"] = testcases

    return render(request, "testcase_table_for_group.html", context)


@require_http_methods(["GET"])
@permission_required("networktests.add_testresult")
def run_testcase(request, group, pk):
    testcase = get_object_or_404(TestCase, pk=pk)
    _ = testcase.run()

    context = {"testcase": testcase, "testgroup_name": group}

    # return list_testcases(request, group)
    return render(request, "single_testcase.html", context)


def get_aval_testcases_for_testgroup(testgroup: TestGroup) -> set:
    already_added = set(testgroup.testcases.get_queryset())
    return set(TestCase.objects.all()) - already_added


@require_http_methods(["GET"])
@permission_required("testgroups.view_testgroup")
def get_testcase_search_popup(request, testgroup_name):
    testgroup = get_object_or_404(TestGroup, name=testgroup_name)
    testcases = get_aval_testcases_for_testgroup(testgroup)

    context = {"testcases": testcases, "testgroup": testgroup}

    return render(request, "testcase_search_popup.html", context)


@require_http_methods(["POST"])
@permission_required("testgroups.view_testgroup")
def get_filtered_testcases(request):
    testgroup_pk = request.POST.get("testgroup")
    search = request.POST.get("search").strip()
    if not testgroup_pk:
        return HttpResponseBadRequest()
    if not search:
        search = ""

    try:
        testgroup = TestGroup.objects.get(pk=testgroup_pk)
    except TestGroup.DoesNotExist:
        return HttpResponseBadRequest("Test group does not exist")

    aval_testcases = get_aval_testcases_for_testgroup(testgroup)

    startingwith_testcases: set[TestCase] = set(
        filter(lambda t: t.label.startswith(search), aval_testcases)
    )
    matching_testcases: set[TestCase] = (
        set(filter(lambda t: search in t.label, aval_testcases))
        - startingwith_testcases
    )

    filtered_testcases = list(startingwith_testcases)
    filtered_testcases.extend(matching_testcases)

    return render(
        request, "popup_testcases_tbody.html", context={"testcases": filtered_testcases}
    )
