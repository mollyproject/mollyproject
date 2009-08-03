# Create your views here.

from xml.etree import ElementTree as ET
import urllib
import ElementSoup as ES

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.http import Http404
from django.shortcuts import get_object_or_404

#from mobile_portal.core.geolocation import distance
from mobile_portal.core.renderers import mobile_render
#from mobile_portal import oxpoints
from mobile_portal.core.models import Feed

from mobile_portal.oxpoints.models import Entity, EntityType
from mobile_portal.oxpoints.entity import get_resource_by_url, MissingResource, Unit, Place

def index(request):
    context = {
        'entity_types': EntityType.objects.all(),
    }
    return mobile_render(request, context, 'maps/index')

    
def nearest(request, ptype, distance=100):
    if not hasattr(request, 'location') or not request.location:
        return mobile_render(request, {}, 'core/require_location')
    entity_type = get_object_or_404(EntityType, slug=ptype)
    
    point = Point(request.location[1], request.location[0], srid=4326)
    
    entities = Entity.objects.filter(entity_type=entity_type, location__distance_lt = (point, D(m=distance)))
    
    for entity in entities:
        entity.distance = D(m=entity.location.transform(27700, clone=True).distance(point.transform(27700, clone=True)))
    entities = sorted(entities, key=lambda e:e.distance)
    
    context = {
        'entity_type': entity_type,
        'entities': entities
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

OXONTIME_URL = 'http://www.oxontime.com/pip/stop.asp?naptan=%s&textonly=1'
def busstop(request, atco_code):
    entity = get_object_or_404(Entity, atco_code=atco_code)
    xml = ES.parse(urllib.urlopen(OXONTIME_URL % atco_code))
    
    try:
        cells = xml.find('.//table').findall('td')[4:]
        rows = [cells[i:i+4] for i in range(0, len(cells), 4)]
    except AttributeError:
        rows = []
        
    print rows
        
    times = []
    for row in rows:
        times.append({
            'service': row[0].text.encode('utf8').replace('\xc2\xa0', ''),
            'destination': row[1].text.encode('utf8').replace('\xc2\xa0', ''),
            'proximity': row[2].text.encode('utf8').replace('\xc2\xa0', ''),
        })
        
    context = {
        'times': times,
        'entity': entity,
    }        
        
    return mobile_render(request, context, 'maps/busstop')
    
def osm(request, osm_node_id):
    entity = get_object_or_404(Entity, osm_node_id=osm_node_id)
    
    context = {
        'entity': entity,
    }
    
    try:
        return mobile_render(request, context, 'maps/osm/%s' % entity.entity_type.slug)
    except:
        return mobile_render(request, context, 'maps/osm/base')
