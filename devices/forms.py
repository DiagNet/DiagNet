from django import forms
from .models import Device


class DeviceForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

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


class UploadFileForm(forms.Form):
    yaml_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )
    Overwrite_Existing_Devices = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
