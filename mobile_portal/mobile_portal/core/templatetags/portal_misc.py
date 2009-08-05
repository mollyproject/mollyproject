from django import template

register = template.Library()

@register.filter(name="gte")
def gte(value, arg):
    return value >= float(arg)