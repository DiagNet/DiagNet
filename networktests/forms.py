from django import forms

from networktests.models import TestCase, TestGroup


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
