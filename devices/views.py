from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from devices.forms import DeviceForm

from .models import Device


class DeviceListView(generic.ListView):
    """Generic class-based view for a list of devices."""

    devices = Device.objects.all()
    model = Device


class DeviceCreate(CreateView):
    model = Device
    form_class = DeviceForm

    def get_success_url(self):
        return reverse_lazy("device-list")


class DeviceUpdate(UpdateView):
    model = Device
    form_class = DeviceForm

    def get_success_url(self):
        return reverse_lazy("device-list")


class DeviceDelete(DeleteView):
    model = Device
    success_url = reverse_lazy("device-list")

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)
        except Exception:
            return HttpResponseRedirect(
                reverse("device-delete", kwargs={"pk": self.object.pk})
            )


def device_check(request, pk):
    device = get_object_or_404(Device, pk=pk)
    status = device.can_connect()
    if status:
        device.status = "reachable"
    else:
        device.status = "unreachable"

    device.save()
    return render(
        request,
        "devices/partials/device_status_cell.html",
        {"status": device.get_status_display()},
    )
