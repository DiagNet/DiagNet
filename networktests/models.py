from django.core.validators import RegexValidator
from django.db import models
from devices.models import Device
import importlib

from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone


class TestCase(models.Model):
    test_module = models.TextField(
        validators=[
            RegexValidator(
                regex=r"^[A-Z][A-Za-z0-9_]*$",
                message="Module name must follow Python class naming convention (PascalCase).",
            )
        ]
    )
    expected_result = models.BooleanField()
    label = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def run(self):
        module = importlib.import_module(f"networktests.testcases.{self.test_module}")
        cls = getattr(module, self.test_module)

        params = {p.name: p.value for p in self.parameters.all()}
        params = params | {p.name: p.device for p in self.devices.all()}

        start = timezone.now()

        test_data = cls().run(**params)

        end = timezone.now()
        result = test_data.get("result") == "PASS"

        self.results.create(
            started_at=start,
            finished_at=end,
            result=result,
            log=test_data,
        )

        return test_data

        if isinstance(result, (list, tuple)):
            return result[0] if result else {"result": "FAIL", "tests": {}}
        elif isinstance(result, dict):
            return result
        elif isinstance(result, bool):
            return {"result": "PASS" if result else "FAIL", "tests": {}}
        elif isinstance(result, int):
            return {"result": "PASS" if result == 1 else "FAIL", "tests": {}}
        else:
            s = str(result).upper()
            if s in ("PASS", "FAIL"):
                return {"result": s, "tests": {}}
            return {"result": str(result), "tests": {}}

    def __str__(self):
        return f"{self.label}"


class TestParameter(models.Model):
    name = models.TextField()
    # All Parameters accessible using test_case.parameters.all()
    # When the parent TestCase is deleted the Parameter is deleted as well.
    test_case = models.ForeignKey(
        TestCase, related_name="parameters", on_delete=models.CASCADE
    )
    value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}: {self.value}"


class TestDevice(models.Model):
    name = models.TextField()
    # All Parameters accessible using test_case.parameters.all()
    # When the parent TestCase is deleted the Parameter is deleted as well.
    test_case = models.ForeignKey(
        TestCase, related_name="devices", on_delete=models.CASCADE
    )
    device = models.ForeignKey(
        to=Device, related_name="device", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.name}: {self.device}"


class TestResult(models.Model):
    attempt_id = models.IntegerField(null=True, blank=True)
    # All Parameters accessible using test_case.results.all()
    # When the parent TestCase is deleted the Parameter is deleted as well.
    test_case = models.ForeignKey(
        TestCase, related_name="results", on_delete=models.CASCADE
    )
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(blank=True, null=True)
    result = models.BooleanField()
    log = models.JSONField(blank=True, null=True)

    # Guarantees that there are not multiple results for the same attempt
    class Meta:
        unique_together = ("attempt_id", "test_case")

    def save(self, *args, **kwargs):
        if self.attempt_id is None:
            last = TestResult.objects.filter(test_case=self.test_case).order_by('-attempt_id').first()
            self.attempt_id = (last.attempt_id + 1) if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Attempt {self.attempt_id} for {self.test_case}"
