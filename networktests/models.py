from django.db import models
from devices.models import Device


class TestCase(models.Model):
    test_module = models.TextField()
    expected_result = models.BooleanField()
    label = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

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
    device = models.ForeignKey(to=Device, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}: {self.device}"


class TestResult(models.Model):
    attempt_id = models.IntegerField()
    # All Parameters accessible using test_case.results.all()
    # When the parent TestCase is deleted the Parameter is deleted as well.
    test_case = models.ForeignKey(
        TestCase, related_name="results", on_delete=models.CASCADE
    )
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(blank=True, null=True)
    result = models.BooleanField()
    log = models.TextField(blank=True, null=True)

    # Guarantees that there are not multiple results for the same attempt
    class Meta:
        unique_together = ("attempt_id", "test_case")

    def __str__(self):
        return f"Attempt {self.attempt_id} for {self.test_case}"
