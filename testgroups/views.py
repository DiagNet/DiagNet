import re
from django.db.utils import IntegrityError
from django.http import HttpResponse
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


testgroup_name_pattern = r"[A-Za-z_-]+"


def create_testgroup(request):
    if request.method != "POST":
        return HttpResponse("Wrong request method")

    name = name = request.POST.get("name")

    error = None
    if not name:
        error = "Name cannot be empty"
    elif not re.fullmatch(testgroup_name_pattern, name):
        error = "Name can only contain letters, underscores (_) and dashes (-)"
    else:
        try:
            tg = TestGroup(name=name)
            tg.save()
        except IntegrityError:
            error = "A group with that name already exists"

    return list_testgroups(request, error=error)
