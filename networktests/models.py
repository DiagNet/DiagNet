from django.db import models

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
    test_case = models.ForeignKey(TestCase, related_name='parameters', on_delete=models.CASCADE)
    value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}: {self.value}"