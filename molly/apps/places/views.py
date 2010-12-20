from __future__ import division

from itertools import chain
import simplejson, copy

from django.contrib.gis.geos import Point
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.template.defaultfilters import capfirst

from molly.utils.views import BaseView, ZoomableView
from molly.utils.breadcrumbs import *
from molly.favourites.views import FavouritableView
from molly.geolocation.views import LocationRequiredView

from molly.osm.utils import fit_to_map
from molly.osm.models import OSMUpdate

from models import Entity, EntityType
from utils import get_entity, get_point
from forms import BusstopSearchForm, UpdateOSMForm


class IndexView(BaseView):
    def get_metadata(self, request):
        return {
            'title': 'places',
            'additional': 'Find University buildings and units, along with bus stops and local amenities',
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            'places',
            None,
            'Places',
            lazy_reverse('index')
        )

    def initial_context(self, request):
        return {
            'return_url': request.get_full_path(),
        }

    def handle_GET(self, request, context):
        return self.render(request, context, 'places/index')

class NearbyListView(LocationRequiredView):
    def get_metadata(self, request, entity=None):
        return {
            'title': 'Find things nearby',
            'additional': 'Search for things based on your current location',
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, entity=None):
        return Breadcrumb(
            'places',
            lazy_parent('index'),
            'Things nearby',
            url = lazy_reverse('nearby-list'),
        )


    def handle_GET(self, request, context, entity=None):
        point = get_point(request, entity)

        if entity:
            return_url = reverse('places:entity-nearby-list', args=[entity.identifier_scheme, entity.identifier_value])
        else:
            return_url = reverse('places:nearby-list')

        entity_types_map = dict((e.slug, e) for e in EntityType.objects.all())
        entity_types = tuple((name, tuple(entity_types_map[t] for t in types)) for (name, types) in self.conf.nearby_entity_types)
        flat_entity_types = set(chain(*[types for name, types in entity_types]))

        entities = Entity.objects.filter(location__isnull = False, all_types_completion__in = flat_entity_types)
        entities = entities.distance(point).order_by('distance')

        for et in flat_entity_types:
            et.max_distance = 0
            et.entities_found = 0

        for e in entities:
            for et in e.all_types_slugs:
                et = entity_types_map[et]
                if not et in flat_entity_types:
                    continue
                if (e.distance.m ** 0.75) * (et.entities_found + 1) > 500:
                    flat_entity_types.remove(et)
                    continue
                et.max_distance = e.distance
                et.entities_found += 1

            if len(flat_entity_types) == 0 or e.distance.m > 5000:
                break

        entity_types = tuple((name, tuple(t for t in types if t.entities_found>0)) for name, types in entity_types)

        context.update({
            'entity_types': entity_types,
            'entity': entity,
            'return_url': return_url,
            'exposes_user_data': entity is None, # entity is None => we've searched around the user's location
        })
        if entity and not entity.location:
            return self.render(request, context, 'places/entity_without_location')
        return self.render(request, context, 'places/nearby_list')


class NearbyDetailView(LocationRequiredView, ZoomableView):
    def initial_context(self, request, ptypes, entity=None):
        point = get_point(request, entity)

        entity_types = tuple(get_object_or_404(EntityType, slug=t) for t in ptypes.split(';'))

        if point:
            entities = Entity.objects.filter(location__isnull = False, is_sublocation = False)
            if ptypes:
                for et in entity_types:
                    entities = entities.filter(all_types_completion=et)
            else:
                entity_types = []
            entities = entities.distance(point).order_by('distance')[:99]
        else:
            entities = []

        context = super(NearbyDetailView, self).initial_context(request, ptypes, entities)
        context.update({
            'entity_types': entity_types,
            'point': point,
            'entities': entities,
            'entity': entity,
            'exposes_user_data': entity is None, # entity is None => point is the user's location
        })
        return context

    @BreadcrumbFactory
    def breadcrumb(self, request, context, ptypes, entity=None):
        title = NearbyDetailView.get_metadata(self, request, ptypes, entity)['title']
        return Breadcrumb('places',
                          lazy_parent('nearby-list'),
                          title,
                          lazy_reverse('nearby-detail', args=[ptypes]))

    def get_metadata(self, request, ptypes, entity=None):
        context = NearbyDetailView.initial_context(self, request, ptypes, entity)

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

    def handle_GET(self, request, context, ptypes, entity=None):

        entity_types, entities, point = (
            context['entity_types'], context['entities'],
            context['point'],
        )

        if entity and not point:
            context = {'entity': entity}
            raise Exception
            return self.render(request, context, 'places/entity_without_location')

        if context['zoom'] is None:
            min_points = 5
        else:
            min_points = 0

        map_hash, (new_points, zoom) = fit_to_map(
            centre_point = (point[0], point[1], 'green'),
            points = ((e.location[0], e.location[1], 'red') for e in entities),
            min_points = min_points,
            zoom = context['zoom'],
            width = request.map_width,
            height = request.map_height,
        )

        entities = [[entities[i] for i in b] for a,b in new_points]

        found_entity_types = set()
        for e in chain(*entities):
            e.bearing = e.get_bearing(point)
            found_entity_types |= set(e.all_types.all())
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
        return self.render(request, context, 'places/nearby_detail')



class EntityDetailView(ZoomableView, FavouritableView):
    default_zoom = 16
    OXPOINTS_URL = 'http://m.ox.ac.uk/oxpoints/id/%s.json'

    def get_metadata(self, request, scheme, value):
        entity = get_entity(scheme, value)
        user_location = request.session.get('geolocation:location')
        distance, bearing = entity.get_distance_and_bearing_from(user_location)
        additional = '<strong>%s</strong>' % capfirst(entity.primary_type.verbose_name)
        if distance:
            additional += ', approximately %.3fkm %s' % (distance/1000, bearing)
        return {
            'title': entity.title,
            'additional': additional,
        }

    def initial_context(self, request, scheme, value):
        context = super(EntityDetailView, self).initial_context(request)
        entity = get_entity(scheme, value)
        context.update({
            'entity': entity,
            'train_station': entity, # This allows the ldb metadata to be portable
            'entity_types': entity.all_types.all(),
        })
        return context

    @BreadcrumbFactory
    def breadcrumb(self, request, context, scheme, value):
        if request.session.get('geolocation:location'):
            parent_view = 'nearby-detail'
        else:
            parent_view = 'category-detail'
        entity = get_entity(scheme, value)
        return Breadcrumb(
            'places',
            lazy_parent(parent_view, ptypes=entity.primary_type.slug),
            context['entity'].title,
            lazy_reverse('entity', args=[scheme,value]),
        )

    def handle_GET(self, request, context, scheme, value):
        entity = context['entity']
        if entity.absolute_url != request.path:
            return HttpResponsePermanentRedirect(entity.absolute_url)

        for provider in reversed(self.conf.providers):
            provider.augment_metadata((entity,))

        return self.render(request, context, 'places/entity_detail')


class EntityUpdateView(ZoomableView):
    default_zoom = 16

    def get_metadata(self, request, scheme, value):
        return {
            'exclude_from_search':True,
        }

    def initial_context(self, request, scheme, value):
        return dict(
            super(EntityUpdateView, self).initial_context(request),
            entity=get_entity(scheme, value),
        )

    @BreadcrumbFactory
    def breadcrumb(self, request, context, scheme, value):
        return Breadcrumb(
            'places',
            lazy_parent('entity', scheme=scheme, value=value),
            'Update place',
            lazy_reverse('entity-update', args=[scheme, value])
        )

    def handle_GET(self, request, context, scheme, value):
        entity = context['entity']
        if entity.source.module_name != 'molly.providers.apps.maps.osm':
            raise Http404

        if request.GET.get('submitted') == 'true':
            return self.render(request, context, 'places/update_osm_done')

        data = dict((k.replace(':','__'), v) for (k,v) in entity.metadata['osm']['tags'].items())

        form = UpdateOSMForm(data)

        context['form'] = form
        return self.render(request, context, 'places/update_osm')

    def handle_POST(self, request, context, scheme, value):
        entity = context['entity'] = get_entity(scheme, value)
        if entity.source.module_name != 'molly.providers.apps.maps.osm':
            raise Http404

        form = UpdateOSMForm(request.POST)
        if form.is_valid():
            new_metadata = copy.deepcopy(entity.metadata['osm'])
            for k in ('name', 'operator', 'phone', 'opening_hours', 'url', 'cuisine', 'food', 'food__hours', 'atm', 'collection_times', 'ref', 'capacity'):
                tag_name = k.replace('__', ':')
                if tag_name in new_metadata and not form.cleaned_data[k]:
                    del new_metadata['osm']['tags'][tag_name]
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

            return HttpResponseRedirect(reverse('places:entity-update', args=[scheme, value])+'?submitted=true')
        else:
            context['form'] = form
            return self.render(request, context, 'places/update_osm')


class NearbyEntityListView(NearbyListView):
    def is_location_required(self, request, scheme, value):
        return False

    def get_metadata(self, request, scheme, value):
        entity = get_entity(scheme, value)
        return super(NearbyEntityListView, self).get_metadata(request, entity)

    def initial_context(self, request, scheme, value):
        return {
            'entity': get_entity(scheme, value),
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, scheme, value):
        return Breadcrumb(
            'places',
            lazy_parent('entity', scheme=scheme, value=value),
            'Things near %s' % context['entity'].title,
            lazy_reverse('entity-nearby-list', args=[scheme, value])
        )

    def handle_GET(self, request, context, scheme, value):
        entity = get_entity(scheme, value)
        return super(NearbyEntityListView, self).handle_GET(request, context, entity)

class NearbyEntityDetailView(NearbyDetailView):
    def is_location_required(self, request, scheme, value, ptype):
        return False

    def initial_context(self, request, scheme, value, ptype):
        entity = get_entity(scheme, value)
        context = super(NearbyEntityDetailView, self).initial_context(request, ptype, entity)
        context['entity'] = entity
        return context

    @BreadcrumbFactory
    def breadcrumb(self, request, context, scheme, value, ptype):
        entity_type = get_object_or_404(EntityType, slug=ptype)
        return Breadcrumb(
            'places',
            lazy_parent('entity-nearby-list', scheme=scheme, value=value),
            '%s near %s' % (
                capfirst(entity_type.verbose_name_plural),
                context['entity'].title,
            ),
            lazy_reverse('places:entity_nearby_detail', args=[scheme, value,ptype])
        )

    def get_metadata(self, request, scheme, value, ptype):
        entity = get_entity(type_slug, id)
        return super(NearbyEntityDetailView, self).get_metadata(request, ptype, entity)

    def handle_GET(self, request, context, scheme, value, ptype):
        entity = get_entity(scheme, value)
        return super(NearbyEntityDetailView, self).handle_GET(request, context, ptype, entity)

class CategoryListView(BaseView):
    def initial_context(self, request):
        entity_types = EntityType.objects.filter(show_in_category_list=True)


        return {
            'entity_types': entity_types,
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            'places',
            lazy_parent('index'),
            'Categories',
            lazy_reverse('category-list'),
        )

    def handle_GET(self, request, context):
        return self.render(request, context, 'places/category_list')

class CategoryDetailView(BaseView):
    def initial_context(self, request, ptypes):
        entity_types = tuple(get_object_or_404(EntityType, slug=t) for t in ptypes.split(';'))

        entities = Entity.objects.filter(is_sublocation=False)
        for entity_type in entity_types:
            entities = entities.filter(all_types_completion=entity_type)
        entities = entities.order_by('title')

        found_entity_types = set()
        for e in entities:
            found_entity_types |= set(e.all_types.all())
        found_entity_types -= set(entity_types)

        return {
            'entity_types': entity_types,
            'count': len(entities),
            'entities': entities,
            'found_entity_types': found_entity_types,
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, ptypes):
        return Breadcrumb(
            'places',
            lazy_parent('category-list'),
            capfirst(context['entity_types'][0].verbose_name_plural),
            lazy_reverse('category-detail', args=[ptypes]),
        )

    def get_metadata(self, request, ptypes):
        context = CategoryDetailView.initial_context(self, request, ptypes)

        if len(context['entity_types']) > 1:
            return {
                'exclude_from_search':True,
                'title': 'All %s' % context['entity_types'][0].verbose_name_plural,
            }

        return {
            'title': 'All %s' % context['entity_types'][0].verbose_name_plural,
            'additional': '<strong>%d %s</strong>' % (
                len(context['entities']),
                context['entity_types'][0].verbose_name_plural,
            ),
        }

    def handle_GET(self, request, context, ptypes):
        return self.render(request, context, 'places/category_detail')

class BusstopSearchView(BaseView):
    def initial_context(self, request):
        return {
            'search_form': BusstopSearchForm(request.GET or None)
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            'places',
            lazy_parent(IndexView),
            'Search bus stops',
            lazy_reverse('places:busstop_search'),
        )

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

        return self.render(request, context, 'places/busstop_search')

class PostCodeDetailView(NearbyDetailView):
    def get_metadata(self, request, post_code, ptypes=None):
        post_code = get_object_or_404(PostCode, post_code = self.add_space(post_code))
        post_code.title = post_code.post_code
        return super(PostCodeDetailView, self).get_metadata(request, ptypes, post_code)

    def initial_context(self, request, post_code, ptypes=None):
        post_code = get_object_or_404(PostCode, post_code = self.add_space(post_code))
        post_code.title = post_code.post_code
        return super(PostCodeDetailView, self).initial_context(request, ptypes, post_code)


    @BreadcrumbFactory
    def breadcrumb(self, request, context, post_code, ptypes=None):
        return Breadcrumb(
            'places',
            lazy_parent(IndexView),
            'Things near %s' % self.add_space(post_code),
            lazy_reverse('places:postcode_detail', args=[post_code, ptypes]),
        )

    def handle_GET(self, request, context, post_code, ptypes=None):
        return super(PostCodeDetailView, self).handle_GET(request, context,  ptypes, None)

    def handlde_GET(self, request, context, post_code, ptypes=None):
        post_code = get_object_or_404(PostCode, post_code = self.add_space(post_code))

        entities = Entity.objects.filter(location__isnull = False, is_sublocation = False)
        if ptypes:
            entity_types = tuple(get_object_or_404(EntityType, slug=t) for t in ptypes.split(';'))
            for et in entity_types:
                entities = entities.filter(all_types=et)
        entities = entities.distance(post_code.location).order_by('distance')[:99]

        context['entities'] = entities
        return self.render(request, context, 'places/postcode_detail')

    def add_space(self, post_code):
        return post_code[:-3] + ' ' + post_code[-3:]

class ServiceDetailView(BaseView):
    """
    A view showing details of a particular transport service leaving from a place
    """
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context, scheme, value, service_id):
        return Breadcrumb(
            'places',
            lazy_parent('entity', scheme=scheme, value=value),
            context['title'],
            lazy_reverse('service-detail', args=[scheme, value, service_id])
        )
    
    def get_metadata(self, request, scheme, value, service_id):
        return {}

    def initial_context(self, request, scheme, value, service_id):
        context = super(ServiceDetailView, self).initial_context(request)
        entity = get_entity(scheme, value)
        
        # Add live information from the providers
        for provider in reversed(self.conf.providers):
            provider.augment_metadata((entity,))
        
        # If we have no way of getting further journey details, 404
        if 'service_details' not in entity.metadata:
            raise Http404
        
        stop_entities = []
        
        # Deal with train service data
        if entity.metadata['service_type'] == 'ldb':
            service = entity.metadata['service_details'](service_id)
            if service is None:
                raise Http404
            
            destinations = [points['callingPoint'][-1]['locationName'] for points in service['subsequentCallingPoints']['callingPointList']]
            
            # Trains can split and join, which makes figuring out the list of
            # calling points a bit difficult. The LiveDepartureBoards documentation
            # details how these should be handled. First, we build a list of all
            # the calling points on the "through" train.
            calling_points = service['previousCallingPoints']['callingPointList'][0]['callingPoint'] if len(service['previousCallingPoints']) else []
            calling_points += [{
                'locationName': service['locationName'],
                'crs': service['crs'],
                'st': service['std'],
                'et': service['etd'] if 'etd' in service else '',
                'at': service['atd'] if 'atd' in service else '',
            }]
            calling_points += service['subsequentCallingPoints']['callingPointList'][0]['callingPoint']
            
            # Then attach joining services to our thorough route in the correct
            # point, but only if there is a list of previous calling points
            if len(service['previousCallingPoints']):
                for points in service['previousCallingPoints']['callingPointList'][1:]:
                    for point in calling_points:
                        if points['callingPoint'][-1]['crs'] == point['crs']:
                            point['joining'] = points['callingPoint']
            
            # And do the same with splitting services
            for points in service['subsequentCallingPoints']['callingPointList'][1:]:
                for point in calling_points:
                    if points['callingPoint'][0]['crs'] == point['crs']:
                        point['splitting'] = { 'destination': points['callingPoint'][-1]['locationName'], 'list': points['callingPoint'] }
            
            # Now get a list of the entities for the stations (if they exist)
            # to plot on a map
            for point in calling_points:
                
                if 'joining' in point:
                    for jpoint in point['joining']:
                        point_entity = Entity.objects.filter(_identifiers__scheme='crs', _identifiers__value=str(jpoint['crs']))
                        if len(point_entity):
                            point_entity = point_entity[0]
                            jpoint['entity'] = point_entity
                            stop_entities.append(point_entity)
                            jpoint['stop_num'] = len(stop_entities)
                
                point_entity = Entity.objects.filter(_identifiers__scheme='crs', _identifiers__value=str(point['crs']))
                if len(point_entity):
                    point_entity = point_entity[0]
                    point['entity'] = point_entity
                    stop_entities.append(point_entity)
                    point['stop_num'] = len(stop_entities)
                
                if 'splitting' in point:
                    for spoint in point['splitting']['list']:
                        point_entity = Entity.objects.filter(_identifiers__scheme='crs', _identifiers__value=str(spoint['crs']))
                        if len(point_entity):
                            point_entity = point_entity[0]
                            spoint['entity'] = point_entity
                            stop_entities.append(point_entity)
                            spoint['stop_num'] = len(stop_entities)
                        
            context.update({
                'entity': entity,
                'train_service': service,
                'train_calling_points': calling_points,
                'title': service['std'] + ' ' + service['locationName'] + ' to ' + ' and '.join(destinations),
            })
        
        map_hash, (new_points, zoom) = fit_to_map(
            centre_point = (entity.location[0], entity.location[1], 'green'),
            points = ((e.location[0], e.location[1], 'red') for e in stop_entities),
            min_points = len(stop_entities),
            zoom = None,
            width = request.map_width,
            height = request.map_height,
        )
        
        context.update({
            'zoom': zoom,
            'map_hash': map_hash
        })
        
        return context

    def handle_GET(self, request, context, scheme, value, service_id):
        return self.render(request, context, 'places/service_details')

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
    * source: Filters by data source; a places provider module name.
    * near: A long,lat pair to order by
    * max_distance: Filters out those more than the specified distance from the point given above.
    * limit: The number of results to return; defaults to 100; capped at 200 (or 1000 if without_metadata specified)
    * offset: The number of results to skip; defaults to 0
    * without_metadata: If 'true', metadata aren't returned. Raises the limit cap.

    It is an error to specify max_distance without near. Entities are ordered
    by name and then DB id; hence the order is deterministic.

    Returns a JSON object with the following attributes:

    * count: The number of entities that survived the filters
    * returned: The number of entities returned once limit and offset were taken into account
    * limit: The limit used. This may differ from that provided when the latter was invalid.
    * offset: The offset used. This may differ as above.
    * entities: A list of entities

    Entities are JSON objects with the following attributes:

    * primary_type: The primary type of the entity
    * all_types: A list containing all types of the object
    * source: The data source for the entity, with the same range as given above
    * url: The location of this resource on this host
    * name: The title of the entity.
    * location: A two-element list containing longitude and latitude
    * metadata: Any further metadata as provided by the data source
    """

    breadcrumb = NullBreadcrumb

    def handle_GET(self, request, context):
        entities = Entity.objects.order_by('title', 'id')
        error = False
        without_metadata = request.GET.get('without_metadata') == 'true'

        limit, offset = request.GET.get('limit', 100), request.GET.get('offset', 0)
        try:
            limit, offset = int(limit), int(offset)
        except (ValueError, TypeError):
            limit, offset = 100, 0
        limit, offset = min(limit, 1000 if without_metadata else 200), max(offset, 0)

        if 'type' in request.GET:
            entities = entities.filter(all_types_completion__slug = request.GET['type'])
        if 'source' in request.GET:
            entities = entities.filter(source__module_name = request.GET['source'])

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
                'primary_type': entity.primary_type.slug,
                'all_types': [et.slug for et in entity.all_types_completion.all()],
                'source': entity.source.module_name,
                'name': entity.title,
                'location': tuple(entity.location) if entity.location else None,
                'url': entity.get_absolute_url(),
            })
            if not without_metadata:
                out[-1]['metadata'] = entity.metadata

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

        return self.render(request, out, None)

