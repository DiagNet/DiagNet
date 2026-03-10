import json
from concurrent.futures import ThreadPoolExecutor

from django.db.models import Count, OuterRef, Subquery

import yaml
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.http import require_POST, require_http_methods
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from devices.forms import DeviceForm, UploadFileForm
from networktests.models import TestCase, TestResult

from .models import Device

STATE_MAP = {
    "unknown": "❓",
    "reachable": "✅",
    "unreachable": "❌",
    "decryption_error": "🔐",
}


def _get_device_testcases(device):
    latest_result = TestResult.objects.filter(test_case=OuterRef("pk")).order_by(
        "-attempt_id"
    )
    return (
        TestCase.objects.filter(devices__device=device)
        .distinct()
        .annotate(
            latest_result=Subquery(latest_result.values("result")[:1]),
        )
    )


@permission_required("devices.view_device", raise_exception=True)
def index(request):
    return render(request, "devices/index.html")


@permission_required("devices.view_device", raise_exception=True)
@require_http_methods(["GET"])
def device_modal_content(request, pk):
    device = get_object_or_404(Device, pk=pk)
    testcases = _get_device_testcases(device)
    return render(
        request,
        "devices/partials/device_modal_content.html",
        {
            "device": device,
            "testcases": testcases,
            "affected_testcases_count": testcases.count(),
            "from_testcase_pk": request.GET.get("from_testcase"),
            "from_device_pk": request.GET.get("from_device"),
        },
    )


@permission_required("devices.view_device", raise_exception=True)
@require_http_methods(["GET"])
def device_detail_partial(request, pk):
    device = get_object_or_404(Device, pk=pk)
    testcases = _get_device_testcases(device)
    context = {"device": device, "testcases": testcases}

    from_testcase = request.GET.get("from_testcase")
    if from_testcase:
        context["from_testcase_pk"] = from_testcase
        return render(
            request, "devices/partials/device_detail_in_testcase_modal.html", context
        )

    return render(request, "devices/partials/device_details.html", context)


class DeviceListView(PermissionRequiredMixin, generic.ListView):
    """Generic class-based view for a list of devices."""

    permission_required = "devices.view_device"
    model = Device
    paginate_by = 25

    def get_queryset(self):
        return Device.objects.annotate(
            affected_testcases_count=Count("device__test_case", distinct=True)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        session_devices = self.request.session.get("devices", {})
        for device in context["device_list"]:
            status = session_devices.get(str(device.pk), {}).get("status", "unknown")
            # Fallback to unknown if status is not in map (e.g. old session data)
            device.session_status = STATE_MAP.get(status, STATE_MAP["unknown"])

        return context


class DeviceCreate(PermissionRequiredMixin, CreateView):
    permission_required = "devices.add_device"
    model = Device
    form_class = DeviceForm
    template_name = "devices/partials/device_form.html"

    def form_valid(self, form):
        try:
            self.object = form.save()
        except ImproperlyConfigured as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        if self.request.headers.get("HX-Request") == "true":
            position = Device.objects.filter(pk__lte=self.object.pk).count()
            page = (position - 1) // DeviceListView.paginate_by + 1
            response = HttpResponse(status=204)
            response["HX-Trigger"] = json.dumps({"deviceCreated": {"page": page}})
            return response
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("devices-page")


class DeviceUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = "devices.change_device"
    model = Device
    form_class = DeviceForm
    template_name = "devices/partials/device_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.is_plaintext:
            context["encryption_state"] = "unencrypted"
        elif self.object.is_decryption_error:
            context["encryption_state"] = "decryption_error"
        else:
            context["encryption_state"] = "valid"
        return context

    def get_success_url(self):
        return reverse_lazy("device-update", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        try:
            self.object = form.save()
        except ImproperlyConfigured as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        if self.request.headers.get("HX-Request") == "true":
            testcases = _get_device_testcases(self.object)
            return render(
                self.request,
                "devices/partials/device_details.html",
                {"device": self.object, "testcases": testcases},
            )
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.headers.get("HX-Request") == "true":
            state = "valid"
            if self.object.is_plaintext:
                state = "unencrypted"
            elif self.object.is_decryption_error:
                state = "decryption_error"

            return render(
                self.request,
                "devices/partials/device_form.html",
                {
                    "form": form,
                    "object": self.object,
                    "encryption_state": state,
                },
            )
        return super().form_invalid(form)


class DeviceDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "devices.delete_device"
    model = Device
    success_url = reverse_lazy("devices-page")

    def delete(self, request, *args, **kwargs):
        self.get_object().delete()
        if request.headers.get("HX-Request") == "true":
            response = HttpResponse(status=204)
            response["HX-Trigger"] = "devicesRefresh"
            return response
        return HttpResponseRedirect(self.success_url)


@require_POST
@permission_required("networktests.add_testresult", raise_exception=True)
def check_all_devices(request):
    """Check connectivity for all devices and store results in session."""
    devices = list(Device.objects.all())

    def _check(device):
        success, error_msg, error_category = device.test_connection()
        if success:
            return device.pk, "reachable"
        elif error_category == "decryption_error":
            return device.pk, "decryption_error"
        else:
            return device.pk, "unreachable"

    session_devices = request.session.get("devices", {})
    reachable = 0
    unreachable = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        for pk, status in executor.map(_check, devices):
            session_devices[str(pk)] = {"status": status}
            if status == "reachable":
                reachable += 1
            else:
                unreachable += 1

    request.session["devices"] = session_devices

    msg = f"Checked {len(devices)} devices: {reachable} reachable, {unreachable} unreachable."
    level = "success" if unreachable == 0 else "warning"

    response = HttpResponse(status=204)
    response["HX-Trigger"] = json.dumps(
        {"devicesRefresh": True, "showMessage": {"message": msg, "level": level}}
    )
    return response


@permission_required("networktests.add_testresult", raise_exception=True)
def device_check(request, pk):
    device = get_object_or_404(Device, pk=pk)

    # We use test_connection to get the detailed error message,
    # allowing us to distinguish decryption failures from connectivity issues.
    success, error_msg, error_category = device.test_connection()

    if success:
        new_status = "reachable"
    elif error_category == "decryption_error":
        new_status = "decryption_error"
    else:
        new_status = "unreachable"

    if "devices" not in request.session:
        request.session["devices"] = {}

    request.session["devices"][str(pk)] = {"status": new_status}
    request.session.modified = True

    response = render(
        request,
        "devices/partials/device_status_cell.html",
        {"status": STATE_MAP[new_status]},
    )

    # Only show popup for decryption errors
    if error_category == "decryption_error":
        trigger_data = {
            "showMessage": {
                "message": error_msg,
                "level": "danger",
            }
        }
        response["HX-Trigger"] = json.dumps(trigger_data)

    return response


@permission_required("devices.view_device", raise_exception=True)
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


@permission_required("devices.view_device", raise_exception=True)
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


@permission_required("devices.add_device", raise_exception=True)
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
