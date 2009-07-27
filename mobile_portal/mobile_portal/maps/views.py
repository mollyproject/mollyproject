# Create your views here.

from xml.etree import ElementTree as ET

from django.http import Http404

from mobile_portal.core.geolocation import distance
from mobile_portal.core.renderers import mobile_render
from mobile_portal import oxpoints
from mobile_portal.core.models import Feed

from mobile_portal.oxpoints.entity import get_resource_by_url, MissingResource, Unit, Place

def index(request):
    context = {}
    return mobile_render(request, context, 'maps/index')
    
def nearest(request, ptype):
    objects = oxpoints.by_type['http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#' + ptype]
    
    nearby = []
    for o in objects:
        d = distance(o, request)
        if not d is None:
            nearby.append( (d, o) )
        
    nearby.sort()
    
    
    context = {
        'type': ptype,
        'nearby': nearby
    }
    return mobile_render(request, context, 'maps/place_list')

OXPOINTS_URL = 'http://m.ox.ac.uk/oxpoints/id/%s'    
def oxpoints_entity(request, id):
    resource = get_resource_by_url(OXPOINTS_URL % id)
    if isinstance(resource, MissingResource):
        raise Http404
    
    context = {
        'resource': resource,
    }

    if isinstance(resource, Unit):
        template_name = 'maps/oxpoints/unit'
    elif isinstance(resource, Place):
        template_name = 'maps/oxpoints/place'
    
    return mobile_render(request, context, template_name)