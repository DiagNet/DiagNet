import re
from django.db.utils import IntegrityError
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from .models import TestGroup
from networktests.models import TestCase
from django.views.decorators.http import require_http_methods


def testgroups_page(request):
    context = {}
    if len(TestGroup.objects.all()) > 0:
        print(len(TestGroup.objects.all()))
        context = {"testgroup_list": list(TestGroup.objects.all())}

    return render(request, "testgroup_page.html", context=context)


def list_testgroups(request, error=None):
    context = {}
    if error:
        context["error"] = error
        print(error)

    if len(TestGroup.objects.all()) > 0:
        context["testgroup_list"] = TestGroup.objects.all()

    return render(request, "list_testgroups.html", context=context)


testgroup_name_pattern = r"[A-Za-z0-9_]+"


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


def delete_testgroup(request):
    if request.method != "POST":
        return HttpResponse("wrong request method.")

    name = request.POST.get("name")

    try:
        TestGroup.objects.get(name=name).delete()
    except TestGroup.DoesNotExist:
        return list_testgroups(request, "a group with that name does not exist.")

    return list_testgroups(request)


def get_testgroup_detail(request, name: str):
    testgroup: TestGroup
    try:
        testgroup = TestGroup.objects.get(name=name)
    except TestGroup.DoesNotExist:
        raise Http404(" This Test Group does not exist")

    context = {"testgroup": testgroup}
    return render(request, "testgroup_detail.html", context)


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
def run_testcase(request, group, pk):
    testcase = get_object_or_404(TestCase, pk=pk)
    _ = testcase.run()

    return list_testcases(request, group)
