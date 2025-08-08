from django.shortcuts import render, redirect
from .models import Device
from .forms import DeviceForm


def device_list(request):
    devices = Device.objects.all()
    return render(request, "devices/list.html", {"devices": devices})


def device_add(request):
    if request.method == "POST":
        form = DeviceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("device_list")
    else:
        form = DeviceForm()
    return render(request, "devices/form.html", {"form": form})
