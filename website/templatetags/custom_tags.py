from django import template
from django.utils.timezone import localtime, now

register = template.Library()

@register.simple_tag
def today_date(format_string):
    return localtime(now()).strftime(format_string)