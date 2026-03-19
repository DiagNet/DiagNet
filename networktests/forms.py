from django import forms

from networktests.models import TestCase, TestGroup


class TestCaseEditForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = ["label", "description"]
        widgets = {
            "label": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Test case name"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional description",
                }
            ),
        }


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
