import simplejson
import urllib
from simplejson.decoder import JSONDecodeError

from django import template

from molly.apps.places.models import Entity

register = template.Library()

@register.filter(name="oxp_id")
def oxp_id(value):
    prefix = 'http://oxpoints.oucs.ox.ac.uk/id/'
    try:
        if value['uri'].startswith(prefix):
            return value['uri'][len(prefix):]
        else:
            return ""
    except:
        return ""

@register.filter(name="load_oxp_json")
def load_oxp_json(value):
    try:
        return simplejson.load(urllib.urlopen(value['uri']+'.json'))[0]
    except JSONDecodeError:
        return {}

@register.filter(name="oxp_portal_url")
def oxp_portal_url(value):
    try:
        return Entity.objects.get(_identifiers__scheme='oxpoints', _identifiers__value=oxp_id(value)).get_absolute_url()
    except Entity.DoesNotExist:
        return ""