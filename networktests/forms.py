import re

from django import forms

from networktests.models import TestCase
from testgroups.models import TestGroup


class TestGroupForm(forms.ModelForm):
    testcases = forms.ModelMultipleChoiceField(
        queryset=TestCase.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Test Cases",
    )

    class Meta:
        model = TestGroup
        fields = ["name", "testcases"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Group name",
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not re.fullmatch(r"[A-Za-z0-9_]+", name):
            raise forms.ValidationError(
                "Name can only contain letters, numbers and underscores."
            )
        return name
