from django import template

register = template.Library()

@register.filter
def externalservicetoken_count(user):
    return user.externalservicetoken_set.filter(authorized=True).count()
