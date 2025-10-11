from django import template
from django.utils import timezone
from datetime import timedelta

from django.utils.timesince import timesince

register = template.Library()


@register.filter
def relative_or_absolute(value):
    if not value:
        return ""
    now = timezone.now()
    delta = now - value
    if delta <= timedelta(days=7):
        return f"{timesince(value, now)} ago"
    return value.strftime("%Y-%m-%d %H:%M")
