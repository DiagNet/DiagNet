from django.db import models
from networktests.models import TestCase


class TestGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)

    testcases = models.ManyToManyField(TestCase)
