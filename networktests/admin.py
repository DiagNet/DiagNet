from django.contrib import admin
from .models import CustomTestTemplate


@admin.register(CustomTestTemplate)
class CustomTestTemplateAdmin(admin.ModelAdmin):
    list_display = ("class_name", "file_name", "is_enabled", "last_seen_at")
    list_filter = ("is_enabled",)
    search_fields = ("class_name", "file_name")
