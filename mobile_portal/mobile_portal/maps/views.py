from __future__ import division

from math import atan2, degrees

from xml.etree import ElementTree as ET
import urllib, rdflib, urllib2, simplejson, StringIO
import ElementSoup as ES

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

#from mobile_portal.core.geolocation import distance
from mobile_portal.core.renderers import mobile_render
#from mobile_portal import oxpoints
from mobile_portal.core.models import Feed
from mobile_portal.core.decorators import require_location, location_required
from mobile_portal.osm.utils import get_generated_map, fit_to_map

from mobile_portal.oxpoints.models import Entity, EntityType
from mobile_portal.oxpoints.entity import get_resource_by_url, MissingResource, Unit, Place

from mobile_portal.maps.utils import get_entity, is_favourite, make_favourite

def index(request):
    context = {
    }
    return mobile_render(request, context, 'maps/index')

def nearby_list(request, entity=None):
    if entity:
        return_url = reverse('maps_entity_nearby_list', args=[entity.entity_type.slug, entity.display_id])
    else:
        return_url = reverse('maps_nearby_list')
        
    context = {
        'entity_types': EntityType.objects.all(),
        'entity': entity,
        'return_url': return_url,
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

def get_zoom(GET):
    try:
        zoom = int(GET['zoom'])
    except (KeyError, ValueError):
        zoom = None
    else:
        zoom = min(max(10, zoom), 18)
    return zoom

def nearby_detail(request, ptype, entity=None):
    zoom = get_zoom(request.GET)
        
    entity_type = get_object_or_404(EntityType, slug=ptype)
    
    if entity:
        point = entity.location
        if not point:
            context = {'entity': entity}
            return mobile_render(request, context, 'maps/entity_without_location')
        location = point[1], point[0]
    else:
        location = request.preferences['location']['location']
        if not location:
            return location_required(request)
        point = Point(location[1], location[0], srid=4326)
    
    if zoom:
        zoom = int(zoom)
        min_points = 0
    else:
        min_points = 5
        
    entities = Entity.objects.filter(entity_type=entity_type, location__isnull = False, is_sublocation = False)
    entities = entities.distance(point).order_by('distance')[:99]

    for e in entities:
        lat_diff, lon_diff = e.location[0] - point[0], e.location[1] - point[1]
        e.bearing = COMPASS_POINTS[int(((90 - degrees(atan2(lon_diff, lat_diff))+22.5) % 360) // 45)]
        
    map_hash, (new_points, zoom) = fit_to_map(
        centre_point = (location[0], location[1], 'green'),
        points = ((e.location[1], e.location[0], 'red') for e in entities),
        min_points = min_points,
        zoom = zoom,
        width = request.device.max_image_width,
        height = request.device.max_image_height,
    )
    
    entities = [[entities[i] for i in b] for a,b in new_points]
    
    context = {
        'entity_type': entity_type,
        'entities': entities,
        'entity': entity,
        'zoom': zoom,
        'map_hash': map_hash,
        'count': sum(map(len, entities)),
    }
    return mobile_render(request, context, 'maps/nearby_detail')



OXPOINTS_URL = 'http://m.ox.ac.uk/oxpoints/id/%s.json'    
def entity_detail_oxpoints(request, entity):
    zoom = get_zoom(request.GET) or 16
    try:
        data = simplejson.load(urllib.urlopen(OXPOINTS_URL % entity.oxpoints_id))[0]
    except urllib2.HTTPError, e:
        if e.code == 404:
            raise Http404
        else:
            raise

    context = {
        'data': data,
        'entity': entity,
        'zoom': zoom,
    }

    return mobile_render(request, context, 'maps/oxpoints')

OXONTIME_URL = 'http://www.oxontime.com/pip/stop.asp?naptan=%s&textonly=1'
def entity_detail_busstop(request, entity):
    zoom = get_zoom(request.GET) or 16
    
    try:
        xml = ES.parse(urllib.urlopen(OXONTIME_URL % entity.atco_code))
    except (TypeError, IOError):
        rows = []
    else:
        try:
            cells = xml.find('.//table').findall('td')
            rows = [cells[i:i+4] for i in range(0, len(cells), 4)]
        except AttributeError:
            rows = []
        
    services = {}
    for row in rows:
        service, destination, proximity = [row[i].text.encode('utf8').replace('\xc2\xa0', '') for i in range(3)]
        
        if not service in services:
            services[service] = (destination, proximity, [])
        else:
            services[service][2].append(proximity)

    services = [(s[0], s[1][0], s[1][1], s[1][2]) for s in services.items()]
    services.sort(key= lambda x: ( ' '*(5-len(x[0]) + (1 if x[0][-1].isalpha() else 0)) + x[0] ))
    services.sort(key= lambda x: 0 if x[2]=='DUE' else int(x[2].split(' ')[0]))
        
    context = {
        'services': services,
        'entity': entity,
        'zoom': zoom,
    }        
        
    return mobile_render(request, context, 'maps/busstop')
    
def entity_detail_osm(request, entity):
    zoom = get_zoom(request.GET) or 16
    
    context = {
        'entity': entity,
        'zoom': zoom,
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

def entity_detail(request, type_slug, id):
    entity = get_entity(type_slug, id)
    entity.is_favourite = is_favourite(request, entity)
    entity_handler = ENTITY_HANDLERS[entity.entity_type.source]
    return entity_handler(request, entity)
    
def entity_nearby_list(request, type_slug, id):
    entity = get_entity(type_slug, id)
    return nearby_list(request, entity)
    
def entity_nearby_detail(request, type_slug, id, ptype):
    entity = get_entity(type_slug, id)
    return nearby_detail(request, ptype, entity)

def entity_favourite(request, type_slug, id):
    entity = get_entity(type_slug, id)
    
    if request.method != 'POST':
        return HttpResponse('', mimetype='text/plain', status=405)
        
    try:
        value = request.POST['is_favourite'] == 'true'
    except KeyError:
        return HttpResponse('', mimetype='text/plain', status=400)
        
    make_favourite(request, entity, value)
    
    if 'no_redirect' in request.POST:
        return HttpResponse('', mimetype='text/plain', status=400)
        
    if 'return_url' in request.POST:
        return HttpResponseRedirect(request.POST['return_url'])
    else:
        return HttpResponseRedirect(entity.get_absolute_url())

def category_list(request):
    entity_types = EntityType.objects.filter(show_in_category_list=True).order_by('verbose_name_plural')
    
    context = {
        'entity_types': entity_types,
    }
    
    return mobile_render(request, context, 'maps/category_list')
        
def category_detail(request, ptype):
    entity_type = get_object_or_404(EntityType, slug=ptype)
    
    entities = entity_type.entity_set.filter(is_sublocation=False).order_by('title')

    context = {
        'entity_type': entity_type,
        'entities': entities,
    }
    
    return mobile_render(request, context, 'maps/category_detail')

def without_location(request):
    entities = Entity.objects.filter(entity_type__source='oxpoints', location__isnull=True)
    
    data = (
        '%d,"%s","%s"\n' % (e.oxpoints_id, e.title.replace('"', r'\"'), e.entity_type.slug) for e in entities
    )
    
    return HttpResponse(data, mimetype='text/csv')