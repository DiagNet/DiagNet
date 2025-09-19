from django.db import models


class TestGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)
