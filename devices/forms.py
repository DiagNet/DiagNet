from django import forms
from .models import Device


# forms.py
class DeviceVendorForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ["vendor"]
        widgets = {
            "vendor": forms.Select(
                attrs={
                    "class": "form-select",
                    "hx-get": "/devices/vendor-form/",
                    "hx-target": "#device-fields",
                    "hx-trigger": "change",
                }
            )
        }


class DeviceForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
        required=False,
    )

    class Meta:
        model = Device
        fields = [
            "name",
            "protocol",
            "ip_address",
            "port",
            "device_type",
            "username",
            "password",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Hostname"}
            ),
            "protocol": forms.Select(
                attrs={"class": "form-select"}
            ),  # better for choice fields
            "ip_address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "IP Address"}
            ),
            "port": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Port"}
            ),
            "device_type": forms.Select(
                attrs={"class": "form-select"}
            ),  # better for choice fields
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Username"}
            ),
        }


class FortigateDeviceForm(forms.ModelForm):
    token = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "API Token",
            }
        ),
        required=True,
        label="API Token",
    )

    class Meta:
        model = Device
        fields = [
            "name",
            "ip_address",
            "token",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Hostname",
                }
            ),
            "ip_address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "IP Address",
                }
            ),
        }

    def save(self, commit=True):
        device = super().save(commit=False)

        device.vendor = "fortinet"

        device.protocol = None
        device.port = 443
        device.device_type = "FortiOS"
        device.username = None
        device.password = None

        if commit:
            device.save()

        return device


class UploadFileForm(forms.Form):
    yaml_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )
    overwrite_existing_devices = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
