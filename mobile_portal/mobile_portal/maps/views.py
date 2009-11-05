from __future__ import division

from xml.etree import ElementTree as ET
from itertools import chain
from datetime import datetime, timedelta
import urllib, rdflib, urllib2, simplejson, StringIO, copy
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

from mobile_portal.osm.models import OSMUpdate
from mobile_portal.oxpoints.models import Entity, EntityType
from mobile_portal.oxpoints.entity import get_resource_by_url, MissingResource, Unit, Place

from mobile_portal.maps.utils import get_entity, is_favourite, make_favourite, get_bearing
from forms import BusstopSearchForm, UpdateOSMForm

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
        
        entity_types = EntityType.objects.filter(show_in_nearby_list=True)
        university = [et for et in entity_types if et.source == 'oxpoints']
        public = [et for et in entity_types if et.source != 'oxpoints']
        
        
        context = {
            'university': university,
            'public': public,
            'entity': entity,
            'return_url': return_url,
        }
        if entity and not entity.location:
            return mobile_render(request, context, 'maps/entity_without_location')
        return mobile_render(request, context, 'maps/nearby_list')

class NearbyDetailView(ZoomableView):
    def initial_context(self, request, ptypes, entity=None):
        entity_types = tuple(get_object_or_404(EntityType, slug=t) for t in ptypes.split(';'))
        
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
            entities = Entity.objects.filter(location__isnull = False, is_sublocation = False)
            for et in entity_types:
                entities = entities.filter(all_types=et)
            entities = entities.distance(point).order_by('distance')[:99]
        else:
            entities = []
        
        context = super(NearbyDetailView, self).initial_context(request, ptypes, entities)
        context.update({
            'entity_types': entity_types,
            'point': point,
            'location': location,
            'entities': entities,
            'entity': entity,
        })
        return context

    def get_metadata(self, request, ptypes, entity=None):
        context = self.initial_context(request, ptypes, entity)
        
        if len(context['entity_types']) > 1:
            return {
                'exclude_from_search':True,
            }
        
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
        
    def handle_GET(self, request, context, ptypes, entity=None):
        entity_types, entities, point, location = (
            context['entity_types'], context['entities'],
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
        
        map_hash, (new_points, zoom) = fit_to_map(
            centre_point = (location[0], location[1], 'green'),
            points = ((e.location[1], e.location[0], 'red') for e in entities),
            min_points = min_points,
            zoom = context['zoom'],
            width = request.device.max_image_width,
            height = request.device.max_image_height,
        )
        
        entities = [[entities[i] for i in b] for a,b in new_points]
        
        found_entity_types = set()    
        for e in chain(*entities):
            e.bearing = get_bearing(point, e.location)
            found_entity_types.add(e.entity_type)
        found_entity_types -= set(entity_types)
        
        context.update({
            'entities': entities,
            'zoom': zoom,
            'map_hash': map_hash,
            'count': sum(map(len, entities)),
            'entity_types': entity_types,
            'found_entity_types': found_entity_types,
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
        context['with_meta_refresh'] = datetime.now() > request.preferences['last_ajaxed'] + timedelta(600)
        
        if request.GET.get('ajax') == 'true':
            request.preferences['last_ajaxed'] = datetime.now()
            context = {
                'services': context['services'],
                'time': datetime.now().strftime('%H:%M:%S'),
            }
            return HttpResponse(simplejson.dumps(context), mimetype='application/json')
        else:
            context['services_json'] = simplejson.dumps(services)
            return mobile_render(request, context, 'maps/busstop')
    
    def display_osm(self, request, context, entity):
        return mobile_render(request, context, 'maps/osm/base')

class EntityUpdateView(ZoomableView):
    default_zoom = 16
    
    def handle_GET(self, request, context, type_slug, id):
        entity = context['entity'] = get_entity(type_slug, id)
        if entity.entity_type.source != 'osm':
            raise Http404
        
        if request.GET.get('submitted') == 'true':
            return mobile_render(request, context, 'maps/update_osm_done')
        
        form = UpdateOSMForm(entity.metadata['tags'])
            
        context['form'] = form
        return mobile_render(request, context, 'maps/update_osm')
        
    def handle_POST(self, request, context, type_slug, id):
        entity = context['entity'] = get_entity(type_slug, id)
        if entity.entity_type.source != 'osm':
            raise Http404

        form = UpdateOSMForm(request.POST)
        if form.is_valid():
            new_metadata = copy.deepcopy(entity.metadata)
            for k in ('name', 'operator', 'phone', 'opening_hours', 'url', 'cuisine', 'food', 'food__hours', 'atm', 'collection_times', 'ref', 'capacity'):
                tag_name = k.replace('__', ':')
                if tag_name in new_metadata and not form.cleaned_data[k]:
                    del new_metadata['tags'][tag_name]
                elif form.cleaned_data[k]:
                    new_metadata['tags'][tag_name] = form.cleaned_data[k]
            
            new_metadata['attrs']['version'] = str(int(new_metadata['attrs']['version'])+1)
            
            osm_update = OSMUpdate(
                contributor_name = form.cleaned_data['contributor_name'],
                contributor_email = form.cleaned_data['contributor_email'],
                contributor_attribute = form.cleaned_data['contributor_attribute'],
                entity = entity,
                old = simplejson.dumps(entity.metadata),
                new = simplejson.dumps(new_metadata),
                notes = form.cleaned_data['notes'],
            )
            osm_update.save()
    
            return HttpResponseRedirect(reverse('maps_entity_update', args=[type_slug, id])+'?submitted=true')
        else:
            context['form'] = form
            return mobile_render(request, context, 'maps/update_osm')


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
        entity_types = EntityType.objects.filter(show_in_category_list=True)
        university = [et for et in entity_types if et.source == 'oxpoints']
        public = [et for et in entity_types if et.source != 'oxpoints']
        
        
        return {
            'university': university,
            'public': public,
        }
    
    def handle_GET(self, request, context):
        return mobile_render(request, context, 'maps/category_list')

class CategoryDetailView(BaseView):
    def initial_context(self, request, ptypes):
        entity_types = tuple(get_object_or_404(EntityType, slug=t) for t in ptypes.split(';'))
        
        entities = Entity.objects.filter(is_sublocation=False)
        for entity_type in entity_types:
            entities = entities.filter(all_types=entity_type)
        entities = entities.order_by('title')
            
        found_entity_types = set()    
        for e in entities:
            found_entity_types.add(e.entity_type)
        found_entity_types -= set(entity_types)

        return {
            'entity_types': entity_types,
            'count': len(entities),
            'entities': entities,
            'found_entity_types': found_entity_types,
        }
    
    def handle_GET(self, request, context, ptypes):
        return mobile_render(request, context, 'maps/category_detail')

class BusstopSearchView(BaseView):
    def initial_context(self, request):
        return {
            'search_form': BusstopSearchForm(request.GET or None)
        }
        
    def handle_GET(self, request, context):
        id = request.GET.get('id', '').strip()
        if len(id) == 5:
            id = '693' + id
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