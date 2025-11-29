from django.core.validators import RegexValidator
from django.db import models
from devices.models import Device
import importlib

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
    description = models.TextField(
        blank=True,
        null=True,
    )

    def getListParameter(self, list_parameter):
        output = []
        list_items = list_parameter.parent_parameter.all()

        for list_item in list_items:
            normal_parameters = list_item.parent_parameter.all()
            device_parameters = list_item.device_parent_parameter.all()

            curr_map = {}
            for p in normal_parameters:
                if p.value == "list":
                    curr_map[p.name] = self.getListParameter(p)
                else:
                    curr_map[p.name] = p.value

            curr_map = curr_map | {p.name: p.device for p in device_parameters}

            output.append(curr_map)

        return output

    def run(self):
        module = importlib.import_module(f"networktests.testcases.{self.test_module}")
        cls = getattr(module, self.test_module)

        params = {}
        for p in self.parameters.all():
            if p.value == "list":
                params[p.name] = self.getListParameter(p)
            else:
                params[p.name] = p.value

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

    def __str__(self):
        return f"{self.label}"


class TestParameter(models.Model):
    name = models.TextField()
    test_case = models.ForeignKey(
        TestCase,
        related_name="parameters",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    value = models.TextField(
        blank=True,
        null=True,
    )
    parent_test_parameter = models.ForeignKey(
        "TestParameter",
        related_name="parent_parameter",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.name}: {self.value}"


class TestDevice(models.Model):
    name = models.TextField()
    test_case = models.ForeignKey(
        TestCase,
        related_name="devices",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    device = models.ForeignKey(
        to=Device,
        related_name="device",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    parent_test_parameter = models.ForeignKey(
        "TestParameter",
        related_name="device_parent_parameter",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.name}: {self.device}"


class TestResult(models.Model):
    attempt_id = models.IntegerField(null=True, blank=True)
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
            last = (
                TestResult.objects.filter(test_case=self.test_case)
                .order_by("-attempt_id")
                .first()
            )
            self.attempt_id = (last.attempt_id + 1) if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Attempt {self.attempt_id} for {self.test_case}"
