from django import template

from molly_oxford.utils.ox_dates import format_today, ox_date_dict

register = template.Library()

@register.simple_tag
def oxford_date_today():
    return format_today()

@register.filter('oxdate')
def oxdate(value, arg):
    return arg % ox_date_dict(value)