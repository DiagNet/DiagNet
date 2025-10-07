from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.http import JsonResponse

from devices.forms import DeviceForm, UploadFileForm

from .models import Device

STATE_MAP = {
    "unknown": "❓",
    "reachable": "✅",
    "unreachable": "❌",
}


class DeviceListView(generic.ListView):
    """Generic class-based view for a list of devices."""

    devices = Device.objects.all()
    model = Device

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        session_devices = self.request.session.get("devices", {})
        for device in context["device_list"]:
            status = session_devices.get(str(device.pk), {}).get("status", "unknown")
            device.session_status = STATE_MAP[status]

        return context


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
    new_status = "reachable" if device.can_connect() else "unreachable"

    if "devices" not in request.session:
        request.session["devices"] = {}

    request.session["devices"][str(pk)] = {"status": new_status}
    request.session.modified = True

    return render(
        request,
        "devices/partials/device_status_cell.html",
        {"status": STATE_MAP[new_status]},
    )


def get_all_devices(request):
    devices = Device.objects.all()
    names = [obj.name for obj in devices]
    return JsonResponse({"results": names})


def handle_uploaded_file(f):
    for l in f:
        print(l)


def import_devices_from_csv(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            print("here")
            handle_uploaded_file(request.FILES["file"])
            return HttpResponseRedirect("/success/url/")
    else:
        form = UploadFileForm()
    return render(request, "upload.html", {"form": form})
