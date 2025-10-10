import re
from django.db.utils import IntegrityError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from .models import TestGroup


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


def list_testcases(request, name: str):
    testgroup: TestGroup
    try:
        testgroup = TestGroup.objects.get(name=name)
    except TestGroup.DoesNotExist:
        raise Http404(" This Test Group does not exist")

    testcases = list(testgroup.testcases.all())
    context = {}
    if len(testcases) > 0:
        context["testcases_list"] = testcases

    return render(request, "list_testcases.html", context)


def add_testcase_to_testgroup(request):
    print(request.POST)
    return HttpResponse()
