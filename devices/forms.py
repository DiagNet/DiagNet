from django import forms
from .models import Device


class DeviceForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
        required=False,
        max_length=256,
    )

    enable_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Enable Password"}
        ),
        required=False,
        max_length=256,
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
            "enable_password",
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

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not password and self.instance.pk:
            return self.instance.password
        return password

    def clean_enable_password(self):
        password = self.cleaned_data.get("enable_password")
        if not password and self.instance.pk:
            return self.instance.enable_password
        return password


class UploadFileForm(forms.Form):
    yaml_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )
    overwrite_existing_devices = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
