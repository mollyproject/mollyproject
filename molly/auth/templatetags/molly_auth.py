from django import template
from django.utils.translation import ungettext

register = template.Library()

@register.filter
def externalservicetoken_count(user):
    count = user.externalservicetoken_set.filter(authorized=True).count()
    return ungettext('%(count)d service', '%(count)d services', count) % {
        'count': count
    }
