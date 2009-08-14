from __future__ import division

from math import atan2, degrees

from xml.etree import ElementTree as ET
import urllib, rdflib, urllib2, simplejson, StringIO
import ElementSoup as ES

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.http import Http404
from django.shortcuts import get_object_or_404

#from mobile_portal.core.geolocation import distance
from mobile_portal.core.renderers import mobile_render
#from mobile_portal import oxpoints
from mobile_portal.core.models import Feed
from mobile_portal.core.decorators import require_location, location_required

from mobile_portal.oxpoints.models import Entity, EntityType
from mobile_portal.oxpoints.entity import get_resource_by_url, MissingResource, Unit, Place

def index(request):
    context = {
    }
    return mobile_render(request, context, 'maps/index')

def nearby_list(request, entity=None):
    context = {
        'entity_types': EntityType.objects.all(),
        'entity': entity,
    }
    if entity and not entity.location:
        return mobile_render(request, context, 'maps/entity_without_location')
    return mobile_render(request, context, 'maps/nearby_list')

DISTANCES = {
    100: '100m',
    200: '200m',
    500: '500m',
    1000: '1km',
    2000: '2km',
    5000: '5km',
    10000: '10km',
}

COMPASS_POINTS = ('N','NE','E','SE','S','SW','W','NW')

def nearby_detail(request, ptype, distance=None, entity=None):
        
    entity_type = get_object_or_404(EntityType, slug=ptype)
    
    if entity:
        point = entity.location
        if not point:
            context = {'entity': entity}
            return mobile_render(request, context, 'maps/entity_without_location')
    else:
        if not (hasattr(request, 'location') and request.location):
            return location_required(request)
        point = Point(request.location[1], request.location[0], srid=4326)
        
    if distance:
        distance = int(distance)
        entities = Entity.objects.filter(entity_type=entity_type, location__distance_lt = (point, D(m=distance)))
    else:
        entities, i = [], 0
        distances = sorted(DISTANCES.keys())
        while i < len(distances) and len(entities) < 5:
            entities = Entity.objects.filter(entity_type=entity_type, location__distance_lt = (point, D(m=distances[i])))
            i += 1
        distance = distances[i - 1]            
    
    for e in entities:
        e.distance = D(m=e.location.transform(27700, clone=True).distance(point.transform(27700, clone=True)))
        lat_diff, lon_diff = e.location[0] - point[0], e.location[1] - point[1]
        e.bearing = COMPASS_POINTS[int(((90 - degrees(atan2(lon_diff, lat_diff))+22.5) % 360) // 45)]
        
    entities = sorted(entities, key=lambda e:e.distance)
    
    context = {
        'entity_type': entity_type,
        'entities': entities,
        'entity': entity,
        'distances': sorted(DISTANCES.items()),
        'distance': DISTANCES.get(distance, (distance < 1000) and ("%dm" % distance) or ("%dkm" % (distance/1000)))
    }
    return mobile_render(request, context, 'maps/nearby_detail')



OXPOINTS_URL = 'http://m.ox.ac.uk/oxpoints/id/%s.json'    
def entity_detail_oxpoints(request, id):
    try:
        data = simplejson.load(urllib.urlopen(OXPOINTS_URL % id))[0]
    except urllib2.HTTPError, e:
        if e.code == 404:
            raise Http404
        else:
            raise

    context = {
        'data': data,
        'entity': get_object_or_404(Entity, oxpoints_id=int(id)),
    }

    return mobile_render(request, context, 'maps/oxpoints')

OXONTIME_URL = 'http://www.oxontime.com/pip/stop.asp?naptan=%s&textonly=1'
def entity_detail_busstop(request, atco_code):
    entity = get_object_or_404(Entity, atco_code=atco_code)
    xml = ES.parse(urllib.urlopen(OXONTIME_URL % atco_code))
    
    try:
        cells = xml.find('.//table').findall('td')[4:]
        rows = [cells[i:i+4] for i in range(0, len(cells), 4)]
    except AttributeError:
        rows = []
        
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
    
def entity_detail_osm(request, osm_node_id):
    entity = get_object_or_404(Entity, osm_node_id=osm_node_id)
    
    context = {
        'entity': entity,
    }
    
    try:
        return mobile_render(request, context, 'maps/osm/%s' % entity.entity_type.slug)
    except:
        return mobile_render(request, context, 'maps/osm/base')


ENTITY_HANDLERS = {
    'osm': entity_detail_osm,
    'naptan': entity_detail_busstop,
    'oxpoints': entity_detail_oxpoints,
}

def get_entity(type_slug, id):
    entity_type = get_object_or_404(EntityType, slug=type_slug)
    id_field = str(entity_type.id_field)
    return get_object_or_404(Entity, **{id_field: id, 'entity_type': entity_type})

def entity_detail(request, type_slug, id):
    entity = get_entity(type_slug, id)
    entity_handler = ENTITY_HANDLERS[entity.entity_type.source]
    return entity_handler(request, id)
    
def entity_nearby_list(request, type_slug, id):
    entity = get_entity(type_slug, id)
    return nearby_list(request, entity)
    
def entity_nearby_detail(request, type_slug, id, ptype, distance=100):
    entity = get_entity(type_slug, id)
    return nearby_detail(request, ptype, distance, entity)