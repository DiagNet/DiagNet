import yaml
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from devices.forms import (
    DeviceForm,
    UploadFileForm,
    FortigateDeviceForm,
    DeviceVendorForm,
)

from .models import Device

STATE_MAP = {
    "unknown": "❓",
    "reachable": "✅",
    "unreachable": "❌",
}


def index(request):
    return render(request, "devices/index.html")


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
    template_name = "devices/partials/device_form.html"

    def get_form_class(self):
        vendor = self.request.POST.get("vendor", "cisco")
        return FortigateDeviceForm if vendor == "fortinet" else DeviceForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 👇 Vendor-Auswahl-Form ins Template geben
        context["vendor_form"] = DeviceVendorForm(
            initial={"vendor": self.request.POST.get("vendor", "cisco")}
        )

        return context

    def form_valid(self, form):
        self.object = form.save()

        if self.request.headers.get("HX-Request") == "true":
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "deviceCreated"
            return response

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("devices-page")


def device_vendor_form(request):
    vendor = request.GET.get("vendor", "cisco")

    if vendor == "fortinet":
        form = FortigateDeviceForm()
        template = "devices/partials/fortigate_fields.html"
    else:
        form = DeviceForm()
        template = "devices/partials/cisco_fields.html"

    return render(request, template, {"form": form})


class DeviceUpdate(UpdateView):
    model = Device
    form_class = DeviceForm
    template_name = "devices/partials/device_form.html"

    def get_success_url(self):
        return reverse_lazy("device-update", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        self.object = form.save()
        if self.request.headers.get("HX-Request") == "true":
            return render(
                self.request,
                "devices/partials/device_details.html",
                {"device": self.object},
            )
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get("HX-Request") == "true":
            return render(
                self.request,
                "devices/partials/device_form.html",
                {"form": form, "object": self.object},
            )
        return super().form_invalid(form)


class DeviceDelete(DeleteView):
    model = Device
    success_url = reverse_lazy("devices-page")

    def delete(self, request, *args, **kwargs):
        self.get_object().delete()
        if request.headers.get("HX-Request") == "true":
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "devicesRefresh"
            return response
        return HttpResponseRedirect(self.success_url)


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


def export_devices_from_yaml(request):
    """
    Exports all devices that are stored in the database into a yaml file.
    """
    import yaml

    devices = Device.objects.all()
    all_data = {}

    for obj in devices:
        data = yaml.safe_load(obj.export_to_yaml())
        all_data.update(data)

    yaml_data = yaml.safe_dump(all_data, sort_keys=False)
    response = HttpResponse(yaml_data, content_type="application/x-yaml")
    response["Content-Disposition"] = 'attachment; filename="devices.yaml"'
    return response


def get_all_devices(request):
    devices = Device.objects.all()
    names = [(obj.name, obj.id) for obj in devices]
    return JsonResponse({"results": names})


def handle_uploaded_file(f, overwrite_existing_devices: bool):
    device_list_yaml: dict = yaml.safe_load(f)
    devices: list[Device] = []

    for name, params in device_list_yaml.items():
        if not overwrite_existing_devices and Device.objects.filter(name=name).exists():
            raise Exception(f'device "{name}" already exists')
        try:
            if Device.objects.filter(name=name).exists():
                device = Device.objects.get(name=name)
                device.name = name
                device.protocol = params["protocol"]
                device.ip_address = params["ip_address"]
                device.port = params["port"]
                device.device_type = params["device_type"]
                device.username = params["username"]
                device.password = params["password"]
                devices.append(device)
                continue
            device = Device(
                name=name,
                protocol=params["protocol"],
                ip_address=params["ip_address"],
                port=params["port"],
                device_type=params["device_type"],
                username=params["username"],
                password=params["password"],
            )
            devices.append(device)
        except Exception as e:
            raise Exception("at device" + name + ", " + str(e))

    for device in devices:
        device.save()

    return True


def import_devices_from_yaml(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                handle_uploaded_file(
                    form.cleaned_data.get("yaml_file"),
                    form.cleaned_data.get("overwrite_existing_devices"),
                )
                return HttpResponseRedirect("/devices/")
            except Exception as e:
                return render(request, "upload.html", {"form": form, "error": e})
    else:
        form = UploadFileForm()
    return render(request, "upload.html", {"form": form})
