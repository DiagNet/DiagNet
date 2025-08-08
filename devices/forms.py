from django import forms
from .models import Device


class DeviceForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Device
        fields = ["name", "ip_address", "device_type", "username", "password"]
