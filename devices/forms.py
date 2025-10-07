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
    title = forms.CharField(max_length=50)
    file = forms.FileField()
