from __future__ import division
from datetime import datetime
from django import template

register = template.Library()

@register.filter
def from_sakai_timestamp(value):
    return datetime.fromtimestamp(value/1000)
