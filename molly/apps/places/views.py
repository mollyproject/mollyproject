from __future__ import division

from collections import defaultdict
from itertools import chain
import simplejson
import copy
import math
from datetime import timedelta

from suds import WebFault

from django.contrib.gis.geos import Point
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.template.defaultfilters import capfirst
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.gis.measure import D

from molly.utils.views import BaseView, ZoomableView
from molly.utils.breadcrumbs import *
from molly.favourites.views import FavouritableView
from molly.geolocation.views import LocationRequiredView

from molly.maps import Map
from molly.maps.osm.models import OSMUpdate

from molly.apps.places.models import Entity, EntityType
from molly.apps.places import get_entity, get_point
from molly.apps.places.forms import UpdateOSMForm


class IndexView(BaseView):

    def get_metadata(self, request):
        return {
            'title': 'places',
            'additional': 'Find University buildings and units, along with' \
                          + ' bus stops and local amenities', }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            'places',
            None,
            'Places',
            lazy_reverse('index'))

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
        
        if point is None:
            return self.render(request, { 'entity': entity },
                               'places/entity_without_location')
        
        if entity:
            return_url = reverse('places:entity-nearby-list',args=[entity.identifier_scheme, entity.identifier_value])
        else:
            return_url = reverse('places:nearby-list')
        
        # Get entity types to show on nearby page
        entity_types = EntityType.objects.filter(show_in_nearby_list=True)
        for et in entity_types:
            # For each et, get the entities that belong to it
            et.max_distance = 0
            et.entities_found = 0
            es = et.entities_completion.filter(location__isnull=False,
                                               location__distance_lt=(point, D(km=5))).distance(point).order_by('distance')
            for e in es:
                if (e.distance.m ** 0.75) * (et.entities_found + 1) > 500:
                    break
                et.max_distance = e.distance.m
                et.entities_found += 1

        categorised_entity_types = defaultdict(list)
        for et in filter(lambda et: et.entities_found > 0, entity_types):
            categorised_entity_types[et.category.name].append(et)
        # Need to do this other Django evalutes .items as ['items']
        categorised_entity_types = dict(categorised_entity_types.items())
        
        context.update({
            'entity_types': categorised_entity_types,
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
                'exclude_from_search': True,
                'title': 'Things near %s' % entity.title,
            }

        if len(context['entity_types']) > 1:
            return {
                'exclude_from_search': True,
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
            return self.render(request, context, 'places/entity_without_location')

        if context['zoom'] is None:
            min_points = 5
        else:
            min_points = 0

        entity_map = Map(
            centre_point = (point[0], point[1], 'green', ''),
            points = [(e.location[0], e.location[1], 'red', e.title)
                for e in entities],
            min_points = min_points,
            zoom = context['zoom'],
            width = request.map_width,
            height = request.map_height,
        )

        entities = [[entities[i] for i in b] for a, b in entity_map.points]

        found_entity_types = set()
        for e in chain(*entities):
            e.bearing = e.get_bearing(point)
            found_entity_types |= set(e.all_types.all())
        found_entity_types -= set(entity_types)

        context.update({
            'entities': entities,
            'map': entity_map,
            'count': sum(map(len, entities)),
            'entity_types': entity_types,
            'found_entity_types': found_entity_types,
        })
        return self.render(request, context, 'places/nearby_detail')


class EntityDetailView(ZoomableView, FavouritableView):
    default_zoom = 16

    def get_metadata(self, request, scheme, value):
        entity = get_entity(scheme, value)
        user_location = request.session.get('geolocation:location')
        distance, bearing = entity.get_distance_and_bearing_from(user_location)
        additional = '<strong>%s</strong>' % capfirst(entity.primary_type.verbose_name)
        if distance:
            additional += ', about %dm %s' % (int(math.ceil(distance/10)*10), bearing)
        return {
            'title': entity.title,
            'additional': additional,
            'entity': entity,
        }

    def initial_context(self, request, scheme, value):
        context = super(EntityDetailView, self).initial_context(request)
        entity = get_entity(scheme, value)
        associations = []
        if hasattr(self.conf, 'associations'):
            for association in self.conf.associations:
                id_type, id, associated_entities = association
                try:
                    if id in entity.identifiers[id_type]:
                        associations += [{'type': type, 'entities': [get_entity(ns, value) for ns, value in es]} for type, es in associated_entities]
                except (KeyError, Http404):
                    pass
        
        for entity_group in entity.groups.all():
            group_entities = filter(lambda e: e != entity,
                                   Entity.objects.filter(groups=entity_group))
            
            if len(group_entities) > 0:
                associations.append({
                    'type': entity_group.title,
                    'entities': group_entities,
                })
        
        board = request.GET.get('board', 'departures')
        if board != 'departures':
            board = 'arrivals'
        
        context.update({
            'entity': entity,
            'train_station': entity, # This allows the ldb metadata to be portable
            'board': board,
            'entity_types': entity.all_types.all(),
            'associations': associations,
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
            lazy_reverse('entity', args=[scheme, value]),
        )

    def handle_GET(self, request, context, scheme, value):
        entity = context['entity']
        
        if entity.absolute_url != request.path:
            return self.redirect(entity.absolute_url, request, 'perm')
        
        entities = []
        for association in context['associations']:
            entities += association['entities']

        for provider in reversed(self.conf.providers):
            provider.augment_metadata((entity, ), board=context['board'])
            provider.augment_metadata([e for atypes in context['associations'] for e in atypes['entities']], board=context['board'])

        return self.render(request, context, 'places/entity_detail')


class EntityUpdateView(ZoomableView):
    default_zoom = 16

    def get_metadata(self, request, scheme, value):
        return {
            'exclude_from_search': True,
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
            lazy_reverse('entity-update', args=[scheme, value]))

    def handle_GET(self, request, context, scheme, value):
        entity = context['entity']
        if entity.source.module_name != 'molly.providers.apps.maps.osm':
            raise Http404

        if request.GET.get('submitted') == 'true':
            return self.render(request, context, 'places/update_osm_done')

        data = dict((k.replace(':', '__'), v) for (k, v) in entity.metadata['osm']['tags'].items())

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

            return self.redirect(
                reverse('places:entity-update', args=[scheme, value]) + '?submitted=true',
                request)
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
            lazy_reverse('entity-nearby-list', args=[scheme, value]))

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
                context['entity'].title, ),
            lazy_reverse('places:entity_nearby_detail', args=[scheme, value, ptype]))

    def get_metadata(self, request, scheme, value, ptype):
        entity = get_entity(type_slug, id)
        return super(NearbyEntityDetailView, self).get_metadata(request, ptype, entity)

    def handle_GET(self, request, context, scheme, value, ptype):
        entity = get_entity(scheme, value)
        return super(NearbyEntityDetailView, self).handle_GET(request, context, ptype, entity)


class CategoryListView(BaseView):

    def initial_context(self, request):
        categorised_entity_types = defaultdict(list)
        for et in EntityType.objects.filter(show_in_category_list=True):
            categorised_entity_types[et.category.name].append(et)
        # Need to do this other Django evalutes .items as ['items']
        categorised_entity_types = dict(categorised_entity_types.items())
        return {
            'entity_types': categorised_entity_types,
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
        return self.render(request, context, 'places/category_list',
                           expires=timedelta(days=28))


class CategoryDetailView(BaseView):

    def initial_context(self, request, ptypes):
        entity_types = tuple(get_object_or_404(EntityType, slug=t) for t in ptypes.split(';'))

        entities = Entity.objects.filter(is_sublocation=False)
        for entity_type in entity_types:
            entities = entities.filter(all_types_completion=entity_type)
        entities = entities.order_by('title')
        
        paginator = Paginator(entities, 100)
        
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        
        try:
            paged_entities = paginator.page(page)
        except (EmptyPage, InvalidPage):
            paged_entities = paginator.page(1)
        
        found_entity_types = set()
        for e in entities:
            found_entity_types |= set(e.all_types.all())
        found_entity_types -= set(entity_types)

        return {
            'entity_types': entity_types,
            'count': len(entities),
            'entities': paged_entities,
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
                'exclude_from_search': True,
                'title': 'All %s' % context['entity_types'][0].verbose_name_plural,
            }

        return {
            'title': 'All %s' % context['entity_types'][0].verbose_name_plural,
            'additional': '<strong>%d %s</strong>' % (
                context['entities'].paginator.count,
                context['entity_types'][0].verbose_name_plural,
            ),
        }

    def handle_GET(self, request, context, ptypes):
        return self.render(request, context, 'places/category_detail',
                           expires=timedelta(days=1))


class ServiceDetailView(BaseView):
    """
    A view showing details of a particular transport service leaving from a place
    """

    @BreadcrumbFactory
    def breadcrumb(self, request, context, scheme, value):
        return Breadcrumb(
            'places',
            lazy_parent('entity', scheme=scheme, value=value),
            context['title'],
            lazy_reverse('service-detail', args=[scheme, value]))

    def get_metadata(self, request, scheme, value):
        return {}

    def initial_context(self, request, scheme, value):

        try:
            service_id = request.GET['id']
        except KeyError:
            raise Http404

        context = super(ServiceDetailView, self).initial_context(request)
        entity = get_entity(scheme, value)

        # Add live information from the providers
        for provider in reversed(self.conf.providers):
            provider.augment_metadata((entity, ))

        # If we have no way of getting further journey details, 404
        if 'service_details' not in entity.metadata:
            raise Http404

        # Deal with train service data
        if entity.metadata['service_type'] == 'ldb':
            
            # LDB has + in URLs, but Django converts that to space
            service = entity.metadata['service_details'](service_id.replace(' ', '+'))
            if service is None:
                raise Http404
            if 'error' in service:
                context.update({
                    'title': 'An error occurred',
                    'entity': entity,
                    'train_service': {
                        'error': service['error'],
                    },
                })
                return context
            
            context.update({
                'entity': entity,
                'train_service': service,
                'title': service['title'],
                'zoom_controls': False,
            })
        
        map = Map(
            centre_point = (entity.location[0], entity.location[1],
                            'green', entity.title),
            points = [(e.location[0], e.location[1], 'red', e.title)
                for e in service['entities']],
            min_points = len(service['entities']),
            zoom = None,
            width = request.map_width,
            height = request.map_height,
        )

        context.update({
            'map': map
        })
        
        return context

    def handle_GET(self, request, context, scheme, value):
        return self.render(request, context, 'places/service_details')

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
