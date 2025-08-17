from django.db import models

class TestCase(models.Model):
    test_module = models.TextField()
    expected_result = models.BooleanField()
    label = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label}"