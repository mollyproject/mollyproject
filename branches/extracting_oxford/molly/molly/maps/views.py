from __future__ import division

from itertools import chain
from datetime import datetime, timedelta
import urllib, urllib2, simplejson, copy

from lxml import etree

from django.contrib.gis.geos import Point
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.template.defaultfilters import capfirst

from molly.utils.renderers import mobile_render
from molly.utils.views import BaseView, ZoomableView
from molly.utils.decorators import location_required
from molly.utils.breadcrumbs import *

from molly.geolocation.views import LocationRequiredView

from molly.osm.utils import get_generated_map, fit_to_map
from molly.osm.models import OSMUpdate
from molly.maps.models import Entity, EntityType, PostCode

from utils import get_entity, is_favourite, make_favourite, get_bearing
from forms import BusstopSearchForm, UpdateOSMForm


class IndexView(BaseView):
    def get_metadata(cls, request):
        return {
            'title': 'Maps',
            'additional': 'Find University buildings and units, along with bus stops and local amenities',
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'maps',
            None,
            'Maps',
            lazy_reverse('maps:index')
        )

    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'maps/index')

class NearbyListView(LocationRequiredView):
    def get_metadata(cls, request, entity=None):
        return {
            'title': 'Find things nearby',
            'additional': 'Search for things based on your current location',
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, entity=None):
        return Breadcrumb(
            'maps',
            lazy_parent(IndexView),
            'Things nearby',
            url = lazy_reverse('maps:nearby_list'),
        )


    def handle_GET(cls, request, context, entity=None):
        if entity:
            return_url = reverse('maps:entity_nearby_list', args=[entity.entity_type.slug, entity.display_id])
        else:
            return_url = reverse('maps:nearby_list')

        entity_types = EntityType.objects.filter(show_in_nearby_list=True)
        university = [et for et in entity_types if et.source == 'oxpoints']
        public = [et for et in entity_types if et.source != 'oxpoints']


        context.update({
            'university': university,
            'public': public,
            'entity': entity,
            'return_url': return_url,
        })
        if entity and not entity.location:
            return mobile_render(request, context, 'maps/entity_without_location')
        return mobile_render(request, context, 'maps/nearby_list')


class NearbyDetailView(LocationRequiredView, ZoomableView):
    def initial_context(cls, request, ptypes, entity=None):
        point, location = None, None
        if entity:
            point = entity.location
            if point:
                location = point[0], point[1]
        else:
            if not request.session.get('geolocation:location'):
                location = None
            else:
                location = request.session.get('geolocation:location')
                if location:
                    print "loc", location
                    point = Point(location[0], location[1], srid=4326)

        entity_types = tuple(get_object_or_404(EntityType, slug=t) for t in ptypes.split(';'))        

        if point:
            entities = Entity.objects.filter(location__isnull = False, is_sublocation = False)
            if ptypes:
                for et in entity_types:
                    entities = entities.filter(all_types=et)
            else:
                entity_types = []
            entities = entities.distance(point).order_by('distance')[:99]
        else:
            entities = []

        context = super(NearbyDetailView, cls).initial_context(request, ptypes, entities)
        context.update({
            'entity_types': entity_types,
            'point': point,
            'location': location,
            'entities': entities,
            'entity': entity,
        })
        return context

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, ptypes, entity=None):
        title = NearbyDetailView.get_metadata(request, ptypes, entity)['title']
        return Breadcrumb('maps',
                          lazy_parent(NearbyListView, entity=entity),
                          title,
                          lazy_reverse('maps:nearby_detail', args=[ptypes]))

    def get_metadata(cls, request, ptypes, entity=None):
        context = NearbyDetailView.initial_context(request, ptypes, entity)

        if len(context['entity_types']) == 0:
            return {
                'exclude_from_search':True,
                'title': 'Things near %s' % entity.title,
            }

        if len(context['entity_types']) > 1:
            return {
                'exclude_from_search':True,
                'title': '%s near%s%s' % (
                    capfirst(context['entity_types'][0].verbose_name_plural),
                    entity and ' ' or '',
                    entity and entity.title or 'by',
                ),
            }

        return {
            'title': '%s near%s%s' % (
                capfirst(context['entity_types'][0].verbose_name_plural),
                entity and ' ' or '',
                entity and entity.title or 'by',
            ),
            'additional': '<strong>%d %s</strong> within 1km' % (
                len([e for e in context['entities'] if e.location.transform(27700, clone=True).distance(context['point'].transform(27700, clone=True)) <= 1000]),
                context['entity_types'][0].verbose_name_plural,
            ),
        }

    def handle_GET(cls, request, context, ptypes, entity=None):
        if not context.get('location'):
            return location_required(request)

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
            points = ((e.location[0], e.location[1], 'red') for e in entities),
            min_points = min_points,
            zoom = context['zoom'],
            width = request.map_width,
            height = request.map_height,
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
        #raise Exception(context)
        return mobile_render(request, context, 'maps/nearby_detail')



class EntityDetailView(ZoomableView):
    default_zoom = 16
    OXPOINTS_URL = 'http://m.ox.ac.uk/oxpoints/id/%s.json'
    OXONTIME_URL = 'http://www.oxontime.com/pip/stop.asp?naptan=%s&textonly=1'

    def get_metadata(cls, request, type_slug, id):
        entity = get_entity(type_slug, id)
        user_location = request.session.get('geolocation:location')
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

    def initial_context(cls, request, type_slug, id):
        context = super(cls, cls).initial_context(request)
        print "F"
        entity = get_entity(type_slug, id)
        context.update({
            'entity': entity,
            'entity_types': [entity.entity_type],
        })
        return context

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, type_slug, id):
        if request.session.get('geolocation:location'):
            parent_view = NearbyDetailView
        else:
            parent_view = CategoryDetailView
        return Breadcrumb(
            'maps',
            lazy_parent(parent_view, ptypes=type_slug),
            context['entity'].title,
            lazy_reverse('maps:entity', args=[type_slug,id]),
        )

    def handle_GET(cls, request, context, type_slug, id):
        entity = context['entity']
        entity.is_favourite = is_favourite(request, entity)
        entity_handler = getattr(cls, 'display_%s' % entity.entity_type.source)
        return entity_handler(request, context, entity)

    def display_oxpoints(cls, request, context, entity):
        try:
            data = simplejson.load(urllib.urlopen(EntityDetailView.OXPOINTS_URL % entity.oxpoints_id))[0]
        except urllib2.HTTPError, e:
            if e.code == 404:
                raise Http404
            else:
                raise

        context['data'] = data

        return mobile_render(request, context, 'maps/oxpoints')

    def display_naptan(cls, request, context, entity):
        try:
            xml = etree.parse(urllib.urlopen(EntityDetailView.OXONTIME_URL % entity.atco_code), parser = etree.HTMLParser())
        except (TypeError, IOError):
            rows = []
        else:
            try:
                cells = xml.find('.//table').findall('td')
                rows = [cells[i:i+4] for i in range(0, len(cells), 4)]
            except AttributeError:
                rows = []
            try:
                context['pip_info'] = xml.find(".//p[@class='pipdetail']").text
            except:
                context['pip_info'] = None

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
        context['with_meta_refresh'] = datetime.now() > request.session.get('core:last_ajaxed', datetime(1970, 1, 1)) + timedelta(600)

        if request.GET.get('ajax') == 'true':
            request.session['core:last_ajaxed'] = datetime.now()
            context = {
                'services': context['services'],
                'time': datetime.now().strftime('%H:%M:%S'),
            }
            return HttpResponse(simplejson.dumps(context), mimetype='application/json')
        else:
            context['services_json'] = simplejson.dumps(services)
            return mobile_render(request, context, 'maps/busstop')

    def display_osm(cls, request, context, entity):
        return mobile_render(request, context, 'maps/osm/base')

    def display_postcode(cls, request, context, entity):
        context['entities'] = Entity.objects.filter(post_code=entity.post_code)
        return mobile_render(request, context, 'maps/postcode')

class EntityUpdateView(ZoomableView):
    default_zoom = 16

    def get_metadata(cls, request, type_slug, id):
        return {
            'exclude_from_search':True,
        }

    def initial_context(cls, request, type_slug, id):
        return dict(
            super(EntityUpdateView, cls).initial_context(request),
            entity=get_entity(type_slug, id),
        )

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, type_slug, id):
        return Breadcrumb(
            'maps',
            lazy_parent(EntityDetailView, type_slug=type_slug, id=id),
            'Things nearby',
            lazy_reverse('maps:entity_update', args=[type_slug,id])
        )

    def handle_GET(cls, request, context, type_slug, id):
        entity = context['entity']
        if entity.entity_type.source != 'osm':
            raise Http404

        if request.GET.get('submitted') == 'true':
            return mobile_render(request, context, 'maps/update_osm_done')

        data = dict((k.replace(':','__'), v) for (k,v) in entity.metadata['tags'].items())

        form = UpdateOSMForm(data)

        context['form'] = form
        return mobile_render(request, context, 'maps/update_osm')

    def handle_POST(cls, request, context, type_slug, id):
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
    def is_location_required(cls, request, type_slug, id):
        return False

    def get_metadata(cls, request, type_slug, id):
        entity = get_entity(type_slug, id)
        return super(NearbyEntityListView, cls).get_metadata(request, entity)

    def initial_context(cls, request, type_slug, id):
        return {
            'entity': get_entity(type_slug, id),
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, type_slug, id):
        return Breadcrumb(
            'maps',
            lazy_parent(EntityDetailView, type_slug=type_slug, id=id),
            'Things near %s' % context['entity'].title,
            lazy_reverse('maps_entity_nearby_list', args=[type_slug,id])
        )

    def handle_GET(cls, request, context, type_slug, id):
        entity = get_entity(type_slug, id)
        return super(NearbyEntityListView, cls).handle_GET(request, context, entity)

class NearbyEntityDetailView(NearbyDetailView):
    def is_location_required(cls, request, type_slug, id):
        return False

    def initial_context(cls, request, type_slug, id, ptype):
        entity = get_entity(type_slug, id)
        context = super(NearbyEntityDetailView, cls).initial_context(request, ptype, entity)
        context['entity'] = entity
        return context

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, type_slug, id, ptype):
        entity_type = get_object_or_404(EntityType, slug=ptype)
        return Breadcrumb(
            'maps',
            lazy_parent(NearbyEntityListView, type_slug=type_slug, id=id),
            '%s near %s' % (
                capfirst(entity_type.verbose_name_plural),
                context['entity'].title,
            ),
            lazy_reverse('maps_entity_nearby_detail', args=[type_slug,id,ptype])
        )

    def get_metadata(cls, request, type_slug, id, ptype):
        entity = get_entity(type_slug, id)
        return super(NearbyEntityDetailView, cls).get_metadata(request, ptype, entity)

    def handle_GET(cls, request, context, type_slug, id, ptype):
        entity = get_entity(type_slug, id)
        return super(NearbyEntityDetailView, cls).handle_GET(request, context, ptype, entity)

class CategoryListView(BaseView):
    def initial_context(cls, request):
        entity_types = EntityType.objects.filter(show_in_category_list=True)
        university = [et for et in entity_types if et.source == 'oxpoints']
        public = [et for et in entity_types if et.source != 'oxpoints']


        return {
            'university': university,
            'public': public,
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'maps',
            lazy_parent(IndexView),
            'Categories',
            lazy_reverse('maps_category_list'),
        )

    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'maps/category_list')

class CategoryDetailView(BaseView):
    def initial_context(cls, request, ptypes):
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

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, ptypes):
        return Breadcrumb(
            'maps',
            lazy_parent(CategoryListView),
            capfirst(context['entity_types'][0].verbose_name_plural),
            lazy_reverse('maps_category_detail', args=[ptypes]),
        )

    def handle_GET(cls, request, context, ptypes):
        return mobile_render(request, context, 'maps/category_detail')

class BusstopSearchView(BaseView):
    def initial_context(cls, request):
        return {
            'search_form': BusstopSearchForm(request.GET or None)
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'maps',
            lazy_parent(IndexView),
            'Search bus stops',
            lazy_reverse('maps_busstop_search'),
        )

    def handle_GET(cls, request, context):
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

class PostCodeDetailView(NearbyDetailView):
    def get_metadata(cls, request, post_code, ptypes=None):
        post_code = get_object_or_404(PostCode, post_code = cls.add_space(post_code))
        post_code.title = post_code.post_code
        return super(PostCodeDetailView, cls).get_metadata(request, ptypes, post_code)

    def initial_context(cls, request, post_code, ptypes=None):
        post_code = get_object_or_404(PostCode, post_code = cls.add_space(post_code))
        post_code.title = post_code.post_code
        return super(PostCodeDetailView, cls).initial_context(request, ptypes, post_code)


    @BreadcrumbFactory
    def breadcrumb(cls, request, context, post_code, ptypes=None):
        return Breadcrumb(
            'maps',
            lazy_parent(IndexView),
            'Things near %s' % cls.add_space(post_code),
            lazy_reverse('maps_postcode_detail', args=[post_code, ptypes]),
        )

    def handle_GET(cls, request, context, post_code, ptypes=None):
        return super(PostCodeDetailView, cls).handle_GET(request, context,  ptypes, None)

    def handlde_GET(cls, request, context, post_code, ptypes=None):
        post_code = get_object_or_404(PostCode, post_code = cls.add_space(post_code))

        entities = Entity.objects.filter(location__isnull = False, is_sublocation = False)
        if ptypes:
            entity_types = tuple(get_object_or_404(EntityType, slug=t) for t in ptypes.split(';'))
            for et in entity_types:
                entities = entities.filter(all_types=et)
        entities = entities.distance(post_code.location).order_by('distance')[:99]

        context['entities'] = entities
        return mobile_render(request, context, 'maps/postcode_detail')

    def add_space(cls, post_code):
        return post_code[:-3] + ' ' + post_code[-3:]

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


class APIView(BaseView):
    """
    Returns a JSON object containing entity details.

    Valid parameters are:

    * type: Filters by an EntityType slug
    * source: Filters by data source; one of 'oxpoints','osm','naptan'
    * near: A long,lat pair to order by
    * max_distance: Filters out those more than the specified distance from the point given above.
    * limit: The number of results to return; defaults to 100; capped at 200
    * offset: The number of results to skip; defaults to 0

    It is an error to specify max_distance without near. Entities are ordered
    by name and then DB id; hence the order is deterministic.

    Returns a JSON object with the following attributes:

    * count: The number of entities that survived the filters
    * returned: The number of entities returned once limit and offset were taken into account
    * limit: The limit used. This may differ from that provided when the latter was invalid.
    * offset: The offset used. This may differ as above.
    * entities: A list of entities

    Entities are JSON objects with the following attributes:

    * type: The primary type of the entity
    * all_types: A list containing all types of the object
    * source: The data source for the entity, with the same domain as given above
    * url: The location of this resource on this host
    * name: The title of the entity.
    * location: A two-element list containing longitude and latitude
    * metadata: Any further metadata as provided by the data source
    """

    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context):
        entities = Entity.objects.order_by('title', 'id')
        error = False

        limit, offset = request.GET.get('limit', 100), request.GET.get('offset', 0)
        try:
            limit, offset = int(limit), int(offset)
        except (ValueError, TypeError):
            limit, offset = 100, 0
        limit, offset = min(limit, 200), max(offset, 0)

        if 'type' in request.GET:
            entities = entities.filter(all_types__slug = request.GET['type'])
        if 'source' in request.GET:
            entities = entities.filter(entity_type__source = request.GET['source'])

        if 'near' in request.GET:
            try:
                point = Point(map(float, request.GET['near'].split(',')), srid=4326).transform(27700, clone=True)

                entities = entities.filter(location__isnull=False)
                entities = entities.distance(point).order_by('distance')

                for entity in entities:
                    entity.distance = entity.location.transform(27700, clone=True).distance(point)

                if 'max_distance' in request.GET:
                    max_distance = float(request.GET['max_distance'])
                    new_entities = []
                    for entity in entities:
                        if entity.distance > max_distance:
                            break
                        new_entities.append(entity)
                    entities = new_entities
                    count = len(entities)

                    if 'limit' in request.GET:
                        entities = islice(entities, offset, offset+limit)
                else:
                    count = entities.count()
            except:
                entities, count, error = [], 0, True
        elif 'max_distance' in request.GET:
            entities, count, error = [], 0, True

        if not 'near' in request.GET:
            count = entities.count()
            try:
                entities = entities[offset:offset+limit]
            except ValueError:
                entities, count, error = [], 0, True

        out = []
        for entity in entities:
            out.append({
                'type': entity.entity_type.slug,
                'all_types': [et.slug for et in entity.all_types.all()],
                'source': entity.entity_type.source,
                'name': entity.title,
                'location': tuple(entity.location),
                'metadata': entity.metadata,
                'url': entity.get_absolute_url(),
            })
            if 'near' in request.GET:
                out[-1]['distance'] = entity.distance

        out = {
            'offset': offset,
            'limit': limit,
            'entities': out,
            'count': count,
            'error': error,
            'returned': len(out),
        }

        return HttpResponse(simplejson.dumps(out), mimetype='application/json')

