from django.http import HttpResponseRedirect
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


class DeviceUpdate(UpdateView):
    model = Device
    form_class = DeviceForm


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
