from __future__ import division

from collections import defaultdict
from itertools import chain
import simplejson
import copy
import math
from urllib import unquote
from datetime import datetime, timedelta, date
from urllib import unquote

from suds import WebFault

from django.contrib.gis.geos import Point
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.template.defaultfilters import capfirst, date as djangodate
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.contrib.gis.measure import D

from molly.utils import haversine
from molly.utils.views import BaseView, ZoomableView
from molly.utils.templatetags.molly_utils import humanise_distance
from molly.utils.breadcrumbs import *
from molly.favourites.views import FavouritableView
from molly.geolocation.views import LocationRequiredView

from molly.maps import Map
from molly.maps.osm.models import OSMUpdate

from molly.routing import generate_route, ALLOWED_ROUTING_TYPES

from molly.apps.places.models import Entity, EntityType, Route, Journey
from molly.apps.places import get_entity, get_point, bus_route_sorter
from molly.apps.places.forms import UpdateOSMForm


class IndexView(BaseView):

    def get_metadata(self, request):
        return {
            'title': _('places'),
            'additional': _('Find University buildings and units, along with bus stops and local amenities'), }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            'places',
            None,
            _('Places'),
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
            'title': _('Find things nearby'),
            'additional': _('Search for things based on your current location'),
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, entity=None):
        return Breadcrumb(
            'places',
            lazy_parent('index'),
            _('Things nearby'),
            url = lazy_reverse('nearby-list'),
        )

    def handle_GET(self, request, context, entity=None):
        point = get_point(request, entity)
        
        if point is None:
            return self.render(request, { 'entity': entity },
                               'places/entity_without_location')
        
        if entity:
            return_url = reverse('places:entity-nearby-list',
                      args=[entity.identifier_scheme, entity.identifier_value])
        else:
            return_url = reverse('places:nearby-list')

        # Get entity types to show on nearby page
        entity_types = EntityType.objects.filter(show_in_nearby_list=True)
        
        for et in entity_types:
            # For each et, get the entities that belong to it
            et.max_distance = humanise_distance(0)
            et.entities_found = 0
            es = et.entities_completion.filter(location__isnull=False,
                                               location__distance_lt=(point, D(km=5))).distance(point).order_by('distance')
            for e in es:
                # Selection criteria for whether or not to count this entity
                if (e.distance.m ** 0.75) * (et.entities_found + 1) > 500:
                    break
                et.max_distance = humanise_distance(e.distance.m)
                et.entities_found += 1

        categorised_entity_types = defaultdict(list)
        for et in filter(lambda et: et.entities_found > 0, entity_types):
            categorised_entity_types[_(et.category.name)].append(et)
        categorised_entity_types = dict(
            (k, sorted(v, key=lambda x: x.verbose_name.lower()))
            for k, v in categorised_entity_types.items())

        context.update({
            'entity_types': categorised_entity_types,
            'entity': entity,
            'return_url': return_url,
            # entity is None => we've searched around the user's location
            'exposes_user_data': entity is None, 
        })
        if entity and not entity.location:
            return self.render(request, context, 'places/entity_without_location')
        return self.render(request, context, 'places/nearby_list')


class NearbyDetailView(LocationRequiredView, ZoomableView):

    def initial_context(self, request, ptypes, entity=None):
        point = get_point(request, entity)

        entity_types = tuple(get_object_or_404(EntityType, slug=t) for t in ptypes.split(';'))

        if point:
            entities = Entity.objects.filter(location__isnull=False)
            for et in entity_types:
                entities = entities.filter(all_types_completion=et)
            
            entities = entities.distance(point).order_by('distance')[:99]
        else:
            entities = []

        context = super(NearbyDetailView, self).initial_context(request, ptypes, entities)
        context.update({
            'entity_types': entity_types,
            'point': point,
            'entities': entities,
            'entity': entity,
            # entity is None => point is the user's location
            'exposes_user_data': entity is None, 
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
                'title': _('Things near %(title)s') % {'title': entity.title}
            }

        et_name = capfirst(context['entity_types'][0].verbose_name_plural)
        if entity is not None:
            title = _('%(entity_type)s near %(entity)s') % {
                                                        'entity_type':et_name,
                                                        'title': entity.title
                                                    }
        else:
            title = _('%(et)s nearby') % {'et': et_name}
            
        if len(context['entity_types']) > 1:
            return {
                'exclude_from_search': True,
                'title': title}
        
        number = len([e for e in context['entities']
                      if haversine(e.location, context['point']) <= 1000])
        entity_type = context['entity_types'][0].verbose_name_plural

        return {
            'title': title,
            'additional': _('<strong>%(number)d %(entity_type)s</strong> within 1km') \
                % {'number': number, 'entity_type': entity_type}
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
        
        # If there are no entities, return a 404. This should only happen if URLs are manually formed by user.
        if len(entities) == 0:
            raise Http404()
        
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
            additional += ', ' + _('about %(distance)s %(bearing)s') % {
                                    'distance': humanise_distance(distance),
                                    'bearing': bearing }
        routes = sorted(set(sor.route.service_id for sor in entity.stoponroute_set.all()),
                        key=bus_route_sorter)
        if routes:
            additional += ', ' + ungettext('service %(services)s stops here',
                                           'services %(services)s stop here',
                                           len(routes)) % {
                                                'services': ' '.join(routes)
                                            }
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

        if unquote(entity.absolute_url) != request.path:
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
            _('Update place'),
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
            _('Things near %s') % context['entity'].title,
            lazy_reverse('entity-nearby-list', args=[scheme, value]))

    def handle_GET(self, request, context, scheme, value):
        entity = context['entity']
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
            _('%(entity_type)s near %(entity)s') % {
                    'entity_type': capfirst(entity_type.verbose_name_plural),
                    'entity': context['entity'].title
                },
            lazy_reverse('places:entity_nearby_detail', args=[scheme, value, ptype]))

    def get_metadata(self, request, scheme, value, ptype):
        entity = get_entity(type_slug, id)
        return super(NearbyEntityDetailView, self).get_metadata(request, ptype, entity)

    def handle_GET(self, request, context, scheme, value, ptype):
        entity = context['entity']
        return super(NearbyEntityDetailView, self).handle_GET(request, context, ptype, entity)


class CategoryListView(BaseView):

    def initial_context(self, request):
        categorised_entity_types = defaultdict(list)
        for et in EntityType.objects.filter(show_in_category_list=True):
            categorised_entity_types[_(et.category.name)].append(et)
        # Need to do this other Django evalutes .items as ['items']
        categorised_entity_types = dict(
            (k, sorted(v, key=lambda x: x.verbose_name.lower()))
            for k, v in categorised_entity_types.items())
        return {
            'entity_types': categorised_entity_types,
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            'places',
            lazy_parent('index'),
            _('Categories'),
            lazy_reverse('category-list'),
        )

    def handle_GET(self, request, context):
        return self.render(request, context, 'places/category_list',
                           expires=timedelta(days=28))


class CategoryDetailView(BaseView):

    def initial_context(self, request, ptypes):
        entity_types = tuple(get_object_or_404(EntityType, slug=t) for t in ptypes.split(';'))

        entities = Entity.objects.all()
        for entity_type in entity_types:
            entities = entities.filter(all_types_completion=entity_type)

        entities = sorted(entities, key=lambda e: e.title)
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

class EntityDirectionsView(LocationRequiredView):
    default_zoom = 16

    def get_metadata(self, request, scheme, value):
        entity = get_entity(scheme, value)
        return {
            'title': _('Directions to %s') % entity.title,
            'entity': entity,
        }

    def initial_context(self, request, scheme, value):
        context = super(EntityDirectionsView, self).initial_context(request)
        entity = get_entity(scheme, value)
        
        allowed_types = ALLOWED_ROUTING_TYPES
        type = request.GET.get('type')
        if type:
            request.session['places:directions-type'] = type
        else:
            type = request.session.get('places:directions-type', 'foot')
        
        if type not in allowed_types:
            type = 'foot'
        
        context.update({
            'entity': entity,
            'type': type,
            'allowed_types': allowed_types,
        })
        return context

    @BreadcrumbFactory
    def breadcrumb(self, request, context, scheme, value):
        entity = get_entity(scheme, value)
        return Breadcrumb(
            'places',
            lazy_parent('entity', scheme=scheme, value=value),
            _('Directions to %s') % context['entity'].title,
            lazy_reverse('entity-directions', args=[scheme, value]),
        )

    def handle_GET(self, request, context, scheme, value):
        
        user_location = request.session.get('geolocation:location')
        if user_location is not None:
            user_location = Point(user_location)
        destination = context['entity'].routing_point(user_location)
        
        if destination.location is not None:
            context['route'] = generate_route([user_location,
                                              destination.location],
                                              context['type'])
            if not 'error' in context['route']:
                context['map'] = Map(
                    (user_location[0], user_location[1], 'green', ''),
                    [(w['location'][0], w['location'][1], 'red', w['instruction'])
                        for w in context['route']['waypoints']],
                    len(context['route']['waypoints']),
                    None,
                    request.map_width,
                    request.map_height,
                    extra_points=[(destination.location[0],
                                   destination.location[1],
                                   'red', destination.title)],
                    paths=[(context['route']['path'], '#3c3c3c')])

        return self.render(request, context, 'places/entity_directions')

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

        context = super(ServiceDetailView, self).initial_context(request)
        
        service_id = request.GET.get('id')
        route_id = request.GET.get('route')
        route_pk = request.GET.get('routeid')
        journey = request.GET.get('journey')
        
        if service_id or route_id or route_pk or journey:
            entity = get_entity(scheme, value)
        else:
            raise Http404()
        
        context.update({
            'entity': entity,
        })
        
        if service_id:
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
            else:
                service = entity.metadata['service_details'](service_id)
            
            if service is None:
                raise Http404
            if 'error' in service:
                context.update({
                    'title': _('An error occurred'),
                    'service': {
                        'error': service['error'],
                    },
                })
                return context

            context.update({
                'service': service,
                'title': service['title'],
                'zoom_controls': False,
            })
        
        elif route_id or route_pk:
            
            if route_id:
            
                route = entity.route_set.filter(service_id=route_id).distinct()
                if route.count() == 0:
                    raise Http404()
                elif route.count() > 1:
                    context.update({
                        'title': _('Multiple routes found'),
                        'multiple_routes': route
                    })
                    return context
                else:
                    route = route[0]
            
            else:
                
                route = get_object_or_404(Route, id=route_pk)
            
            i = 1
            calling_points = []
            previous = True
            for stop in route.stoponroute_set.all():
                if stop.entity == entity:
                    previous = False
                calling_point = {
                    'entity': stop.entity,
                    'at': previous,
                    #'activity': stop.activity
                }
                if stop.entity.location is not None:
                    calling_point['stop_num'] = i
                    i += 1
                calling_points.append(calling_point)
            service = {
                    'entities': route.stops.all(),
                    'operator': route.operator,
                    'has_timetable': False,
                    'has_realtime': False,
                    'calling_points': calling_points
                }
            if entity not in service['entities']:
                raise Http404()
            context.update({
                'title': '%s: %s' % (route.service_id, route.service_name),
                'service': service                
            })
        
        elif journey:
            
            journey = get_object_or_404(Journey, id=journey)
            route = journey.route
            entity_passed = False
            i = 1
            calling_points = []
            
            for stop in journey.scheduledstop_set.all():
                
                if stop.entity == entity:
                    entity_passed = True
                
                if not entity_passed and stop.std < datetime.now().time():
                    
                    calling_point = {
                        'entity': stop.entity,
                        'st': stop.std.strftime('%H:%M'),
                        'at': True,
                        'activity': stop.activity
                    }
                
                else:
                    
                    calling_point = {
                        'entity': stop.entity,
                        # Show arrival time (if it exists, else departure time)
                        # if this stop is AFTER where we currently are, otherwise
                        # show the time the bus left stops before this one (if
                        # it exists)
                        'st': ((stop.sta or stop.std) if entity_passed else (stop.std or stop.sta)).strftime('%H:%M'),
                        'at': False,
                        'activity': stop.activity
                    }
                
                if stop.entity.location is not None:
                    calling_point['stop_num'] = i
                    i += 1
                calling_points.append(calling_point)
            
            service = {
                    'entities': [s.entity for s in journey.scheduledstop_set.all()],
                    'operator': journey.route.operator,
                    'has_timetable': True,
                    'has_realtime': False,
                    'calling_points': calling_points,
                    'notes': journey.notes
                }
            if entity not in service['entities']:
                raise Http404()
            context.update({
                'title': '%s: %s' % (route.service_id, route.service_name),
                'service': service                
            })
        
        if entity.location or len(filter(lambda e: e.location is not None, service['entities'])):
            map = Map(
                centre_point = (entity.location[0], entity.location[1],
                                'green', entity.title) if entity.location else None,
                points = [(e.location[0], e.location[1], 'red', e.title)
                    for e in service['entities'] if e.location is not None],
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


class RouteView(BaseView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context, route, id):
        return Breadcrumb(
            'places',
            lazy_parent('index'),
            context['title'],
            lazy_reverse('route', args=[route, id]))
    
    def initial_context(self, request, route, id):
        
        context = super(RouteView, self).initial_context(request)
        
        if id is None:
            
            context.update({
                'title': _('Select a route'),
                'multiple_routes': Route.objects.filter(service_id=route)
            })
            
        else:
            
            route = get_object_or_404(Route, id=id)
            
            i = 1
            calling_points = []
            
            for stop in route.stoponroute_set.all():
                
                calling_point = {'entity': stop.entity}
                if stop.entity.location is not None:
                    calling_point['stop_num'] = i
                    i += 1
                calling_points.append(calling_point)
            
            service = {
                    'entities': route.stops.all(),
                    'operator': route.operator,
                    'has_timetable': False,
                    'has_realtime': False,
                    'calling_points': calling_points
                }
            
            context.update({
                'title': '%s: %s' % (route.service_id, route.service_name),
                'service': service,
                'route': route
            })
        
        return context
    
    def handle_GET(self, request, context, route, id):
        
        if len(context.get('multiple_routes', [])) == 1:
            # Only one alternative, redirect straight there
            route = context['multiple_routes'][0]
            return self.redirect(reverse('places:route', args=[route.service_id,
                                                               route.pk]), request)
        
        elif id is not None and route != context['route'].service_id:
            # Redirect if the route doesn't match the ID
            return self.redirect(reverse('places:route', args=[context['route'].service_id, id]), request)
        else:
            return self.render(request, context, 'places/service_details')


class TimetableView(BaseView):
    """
    A view which shows the timetable of all departures for a stop.
    """
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context, scheme, value, year, month, day):
        return Breadcrumb(
            'places',
            lazy_parent('entity', scheme=scheme, value=value),
            context['title'],
            lazy_reverse('timetable', args=[scheme, value]))
    
    def initial_context(self, request, scheme, value, year, month, day):
        
        context = super(TimetableView, self).initial_context(request)
        
        context['entity'] = get_entity(scheme, value)
        
        if year and month and day:
            try:
                context['date'] = date(int(year), int(month), int(day))
            except ValueError:
                raise Http404()
        else:
            context['date'] = date.today()
        
        if context['entity'].scheduledstop_set.all().count() == 0:
            # 404 on entities which don't have timetables
            raise Http404()
        
        services = context['entity'].scheduledstop_set.filter(
           journey__runs_from__lte=context['date'],
            journey__runs_until__gte=context['date']
        ).exclude(activity__in=('D','N','F')).order_by('std')
        
        context['timetable'] = filter(lambda s: s.journey.runs_on(context['date']),
                                      services)
        
        context['title'] = _('Timetable for %(title)s on %(date)s') % {
            'title': context['entity'].title,
            'date': djangodate(context['date'])
        }
        
        return context
    
    def handle_GET(self, request, context, scheme, value, year, month, day):
        
        return self.render(request, context, 'places/timetable')
