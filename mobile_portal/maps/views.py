# Create your views here.

from mobile_portal.core.geolocation import distance
from mobile_portal.core.renderers import mobile_render
from mobile_portal import oxpoints


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
        'nearby': nearby
    }
    return mobile_render(request, context, 'maps/place_list')