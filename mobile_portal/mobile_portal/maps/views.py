from __future__ import division

from xml.etree import ElementTree as ET
import urllib, rdflib, urllib2, simplejson, StringIO
import ElementSoup as ES

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.template.defaultfilters import capfirst

#from mobile_portal.core.geolocation import distance
from mobile_portal.core.renderers import mobile_render
#from mobile_portal import oxpoints
from mobile_portal.core.handlers import BaseView, ZoomableView
from mobile_portal.core.models import Feed
from mobile_portal.core.decorators import require_location, location_required
from mobile_portal.osm.utils import get_generated_map, fit_to_map

from mobile_portal.oxpoints.models import Entity, EntityType
from mobile_portal.oxpoints.entity import get_resource_by_url, MissingResource, Unit, Place

from mobile_portal.maps.utils import get_entity, is_favourite, make_favourite, get_bearing
from forms import BusstopSearchForm

class IndexView(BaseView):
    def get_metadata(self, request):
        return {
            'title': 'Maps',
            'additional': 'Find University buildings and units, along with bus stops and local amenities',
        }
        
    def handle_GET(self, request, context):
        return mobile_render(request, context, 'maps/index')

class NearbyListView(BaseView):
    def get_metadata(self, request, entity=None):
        return {
            'title': 'Find things nearby',
            'additional': 'Search for things based on your current location',
        }

    def handle_GET(self, request, context, entity=None):
        if entity:
            return_url = reverse('maps_entity_nearby_list', args=[entity.entity_type.slug, entity.display_id])
        else:
            return_url = reverse('maps_nearby_list')
            
        context = {
            'entity_types': EntityType.objects.filter(show_in_nearby_list=True),
            'entity': entity,
            'return_url': return_url,
        }
        if entity and not entity.location:
            return mobile_render(request, context, 'maps/entity_without_location')
        return mobile_render(request, context, 'maps/nearby_list')

class NearbyDetailView(ZoomableView):
    def initial_context(self, request, ptype, entity=None):
        entity_type = get_object_or_404(EntityType, slug=ptype)
        
        point, location = None, None
        if entity:
            point = entity.location
            if point:
                location = point[1], point[0]
        else:
            location = request.preferences['location']['location']
            if location:
                point = Point(location[1], location[0], srid=4326)

        if point:
            entities = Entity.objects.filter(entity_type=entity_type, location__isnull = False, is_sublocation = False)
            entities = entities.distance(point).order_by('distance')[:99]
        else:
            entities = []
        
        context = super(NearbyDetailView, self).initial_context(request, ptype, entities)
        context.update({
            'entity_type': entity_type,
            'point': point,
            'location': location,
            'entities': entities,
            'entity': entity,
        })
        return context

    def get_metadata(self, request, ptype, entity=None):
        context = self.initial_context(request, ptype, entity)
        
        return {
            'title': '%s near%s%s' % (
                capfirst(context['entity_type'].verbose_name_plural),
                entity and ' ' or '',
                entity and entity.title or 'by',
            ),
            'additional': '<strong>%d %s</strong> within 1km' % (
                len([e for e in context['entities'] if e.location.transform(27700, clone=True).distance(context['point'].transform(27700, clone=True)) <= 1000]),
                context['entity_type'].verbose_name_plural,
            ),
        }
        
    def handle_GET(self, request, context, ptype, entity=None):
        entity_type, entities, point, location = (
            context['entity_type'], context['entities'],
            context['point'], context['location'],
        )

        if entity and not (point and location):
            context = {'entity': entity}
            return mobile_render(request, context, 'maps/entity_without_location')
        elif not (point and location):
            return location_required(request)
            
        if context['zoom'] is None:
            min_points = 5
        else:
            min_points = 0
            
        for e in entities:
            e.bearing = get_bearing(point, e.location)
            
        map_hash, (new_points, zoom) = fit_to_map(
            centre_point = (location[0], location[1], 'green'),
            points = ((e.location[1], e.location[0], 'red') for e in entities),
            min_points = min_points,
            zoom = context['zoom'],
            width = request.device.max_image_width,
            height = request.device.max_image_height,
        )
        
        entities = [[entities[i] for i in b] for a,b in new_points]
        
        context.update({
            'entities': entities,
            'zoom': zoom,
            'map_hash': map_hash,
            'count': sum(map(len, entities)),
        })
        return mobile_render(request, context, 'maps/nearby_detail')

    

class EntityDetailView(ZoomableView):
    default_zoom = 16
    OXPOINTS_URL = 'http://m.ox.ac.uk/oxpoints/id/%s.json'
    OXONTIME_URL = 'http://www.oxontime.com/pip/stop.asp?naptan=%s&textonly=1'

    def get_metadata(self, request, type_slug, id):
        entity = get_entity(type_slug, id)
        user_location = request.preferences['location']['location']
        if user_location and entity.location:
            user_location = Point(user_location[1], user_location[0], srid=4326)
            bearing = ', approximately %.3fkm %s' % (
                user_location.transform(27700, clone=True).distance(entity.location.transform(27700, clone=True))/1000,
                get_bearing(user_location, entity.location),
            )
        else:
            bearing = ''
        return {
            'title': entity.title,
            'additional': '<strong>%s</strong>%s' % (
                capfirst(entity.entity_type.verbose_name),
                bearing,
            ),
        }
    
    def handle_GET(self, request, context, type_slug, id):
        entity = context['entity'] = get_entity(type_slug, id)
        entity.is_favourite = is_favourite(request, entity)
        entity_handler = getattr(self, 'display_%s' % entity.entity_type.source)
        return entity_handler(request, context, entity)

    def display_oxpoints(self, request, context, entity):
        try:
            data = simplejson.load(urllib.urlopen(EntityDetailView.OXPOINTS_URL % entity.oxpoints_id))[0]
        except urllib2.HTTPError, e:
            if e.code == 404:
                raise Http404
            else:
                raise
    
        context['data'] = data
    
        return mobile_render(request, context, 'maps/oxpoints')

    def display_naptan(self, request, context, entity):
        try:
            xml = ES.parse(urllib.urlopen(EntityDetailView.OXONTIME_URL % entity.atco_code))
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
            
        context['services'] = services
            
        return mobile_render(request, context, 'maps/busstop')
    
    def display_osm(self, request, context, entity):
        return mobile_render(request, context, 'maps/osm/base')

class NearbyEntityListView(NearbyListView):
    def get_metadata(self, request, type_slug, id):
        entity = get_entity(type_slug, id)
        return super(NearbyEntityListView, self).get_metadata(request, entity)

    def handle_GET(self, request, context, type_slug, id):
        entity = get_entity(type_slug, id)
        return super(NearbyEntityListView, self).handle_GET(request, context, entity)
    
class NearbyEntityDetailView(NearbyDetailView):
    def initial_context(self, request, type_slug, id, ptype):
        entity = get_entity(type_slug, id)
        context = super(NearbyEntityDetailView, self).initial_context(request, ptype, entity)
        context['entity'] = entity
        return context
        
    def get_metadata(self, request, type_slug, id, ptype):
        entity = get_entity(type_slug, id)
        return super(NearbyEntityDetailView, self).get_metadata(request, ptype, entity)

    def handle_GET(self, request, context, type_slug, id, ptype):
        entity = get_entity(type_slug, id)
        return super(NearbyEntityDetailView, self).handle_GET(request, context, ptype, entity)

class CategoryListView(BaseView):
    def initial_context(self, request):
        entity_types = EntityType.objects.filter(show_in_category_list=True).order_by('verbose_name_plural')
        return {
            'entity_types': entity_types,
        }
    
    def handle_GET(self, request, context):
        return mobile_render(request, context, 'maps/category_list')

class CategoryDetailView(BaseView):
    def initial_context(self, request, ptype):
        entity_type = get_object_or_404(EntityType, slug=ptype)
        entities = entity_type.entity_set.filter(is_sublocation=False).order_by('title')
        return {
            'entity_type': entity_type,
            'entities': entities,
        }
    
    def handle_GET(self, request, context, ptype):
        return mobile_render(request, context, 'maps/category_detail')

class BusstopSearchView(BaseView):
    def initial_context(self, request):
        return {
            'search_form': BusstopSearchForm(request.GET or None)
        }
        
    def handle_GET(self, request, context):
        id = request.GET.get('id', '')
        if len(id) == 2:
            entities = Entity.objects.filter(central_stop_id=id.upper())
        elif len(id) == 8:
            entities = Entity.objects.filter(naptan_code=id)
        else:
            entities = []
        
        entities = list(entities)
        if len(entities) == 1:
            return HttpResponseRedirect(entities[0].get_absolute_url())
        
        context['entities'] = entities
        
        return mobile_render(request, context, 'maps/busstop_search')
        
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


def without_location(request):
    entities = Entity.objects.filter(entity_type__source='oxpoints', location__isnull=True)
    
    data = (
        '%d,"%s","%s"\n' % (e.oxpoints_id, e.title.replace('"', r'\"'), e.entity_type.slug) for e in entities
    )
    
    return HttpResponse(data, mimetype='text/csv')