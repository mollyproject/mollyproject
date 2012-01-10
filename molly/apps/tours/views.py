from datetime import datetime
from operator import attrgetter

from django.core.urlresolvers import reverse
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import connection
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.http import Http404

from molly.apps.places import get_entity
from molly.apps.places.models import Entity, EntityType, StopOnRoute
from molly.maps import Map
from molly.utils.breadcrumbs import *
from molly.utils.views import BaseView
from molly.wurfl import device_parents
from molly.routing import generate_route, optimise_points
from molly.apps.tours.models import Tour, StopOnTour
from molly.url_shortener import get_shortened_url


class IndexView(BaseView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            _('Tours'),
            lazy_reverse('index'),
        )
    
    def initial_context(self, request):
        context = super(IndexView, self).initial_context(request)
        
        context['types'] = [(slug, vs['name']) for slug, vs in self.conf.types.items()]
        
        if 'tours:visited' in request.session:
            context.update({
                'tours': Tour.objects.filter(id__in=request.session['tours:visited'])
            })
        
        return context
    
    def handle_GET(self, request, context):
        return self.render(request, context, 'tours/index')


class CreateView(BaseView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context, slug, entities):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            _('Create a tour'),
            lazy_reverse('create'),
        )
    
    def initial_context(self, request, slug, entities):
        context = super(CreateView, self).initial_context(request)
        
        try:
            tour_type = self.conf.types[slug]
        except KeyError:
            raise Http404()
        else:
            tour_type['slug'] = slug
        
        context.update({
            'tour_type': tour_type,
            'entities': [],
            'attractions': dict(
                (et, sorted(et.entities_completion.filter(location__isnull=False),
                            key=attrgetter('title')))
                    for et in EntityType.objects.filter(
                        slug__in=tour_type['attraction_types'])),
            'all_pois': sorted(Entity.objects.filter(
                all_types_completion__slug__in=tour_type['attraction_types']),
                key=attrgetter('title'))
        })
        
        for entity in entities.split('/'):
            try:
                scheme, value = entity.split(':')
            except ValueError:
                continue
            context['entities'].append(get_entity(scheme, value))
        
        return context
    
    def handle_GET(self, request, context, slug, entities):
        
        if 'generic_web_browser' in device_parents[request.browser.devid]:
            # Desktop
            return self.render(request, context, 'tours/create_desktop')
        else:
            return self.render(request, context, 'tours/create')


class SaveView(CreateView):
    
    def handle_GET(self, request, context, slug, entities):
        
        if len(context['entities']) < 2:
            # Need at least 2 entities to be a tour
            return self.bad_request(request)
        
        # Now attempt to order entities optimally
        if len(context['entities']) > 2 and len(context['entities']) <= 10:
            context['entities'] = optimise_points(
                [(entity, entity.routing_point().location)
                    for entity in context['entities']])
            context['optimised_entities'] = True
        
        # Come up with a name for this tour
        name = _('%(type)s; visiting %(number)d places (created on %(creation)s)') % {
                    'type': _(context['tour_type']['name']),
                    'number': len(context['entities']),
                    'creation': datetime.now().strftime('%c')
                }
        
        # Save back to database
        tour = Tour.objects.create(name=name, type=context['tour_type']['slug'])
        for i, entity in enumerate(context['entities']):
            StopOnTour.objects.create(entity=entity, tour=tour, order=i)
        
        # Add any suggested "passing-by" entities to the context to be presented
        # back to the user. We can only do this query if the database backend
        # supports distance operations on geographies (i.e., things more complex
        # than points)
        if 'suggested_entities' in context['tour_type'] \
        and connection.ops.geography and request.GET.get('nosuggestions') is None:
            route = generate_route([e.location for e in context['entities']], 'foot')
            suggestion_filter = Q()
            for sv in context['tour_type']['suggested_entities']:
                scheme, value = sv.split(':')
                suggestion_filter |= Q(_identifiers__scheme=scheme,
                                       _identifiers__value=value)
            context['suggestions'] = Entity.objects.filter(
                suggestion_filter,
                location__distance_lt=(route['path'],
                        D(m=getattr(self.conf, 'suggestion_distance', 100)))
                ).exclude(id__in=[e.pk for e in context['entities']])
        
        context.update({
            'tour': tour,
            'short_url': get_shortened_url(tour.get_absolute_url(), request),
        })
        
        if 'generic_web_browser' in device_parents[request.browser.devid]:
            # Desktop
            return self.render(request, context, 'tours/save_desktop')
        else:
            # Redirect if no suggestions, otherwise show suggestions page
            if len(context.get('suggestions', [])) > 0:
                return self.render(request, context, 'tours/save')
            else:
                return self.redirect(
                    context['tour'].get_absolute_url() + '?created', request)


class TourView(BaseView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context, tour, page=None):
        
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            context['stop'].entity.title if page else context['tour'].name,
            lazy_reverse('tour', args=(context['tour'].pk, page)),
        )
    
    def arrival_route_location(self, first_stop, arrival_route):
        """
        Given a route which the user is entering the city by, then suggest the
        best place to get off the route, and directions from that point to the
        first stop
        """
        
        closest_stop = Entity.objects.filter(
                    stoponroute__route__service_id=arrival_route,
                ).distance(first_stop.location).order_by('distance')
        if closest_stop.count() > 0:
            closest_stop = closest_stop[0]
            start_location = closest_stop
        else:
            start_location = None
        return start_location
    
    def arrival_point_location(self, first_stop, arrival_point):
        """
        Given an arrival point (which may be a park and ride, in which case
        directions using public transport are given), figure out directions to
        the first location
        """
        
        sv, p_and_r, routes = self.conf.arrival_points[int(arrival_point)]
        entity = get_entity(*sv.split(':'))
        if p_and_r:
            
            # Get closest bus stop to first stop on route
            closest_stops = Entity.objects.filter(
                    stoponroute__route__service_id__in=routes,
                ).distance(first_stop.location).order_by('distance')
            
            # Now, check that this stop comes *after* where we get on
            closest_stop = None
            
            # Go through all of our stops until we find the closest
            # one which matches our criteria
            for stop in closest_stops:
                
                # Now, check for each route that goes through this
                # stop that are the ones we're considering
                for route in stop.route_set.filter(service_id__in=routes):
                    
                    stoponroute = StopOnRoute.objects.get(entity=stop,
                                                          route=route)
                    
                    # Get the closest stop to the origin that serves
                    # this route
                    closest_origin = Entity.objects.filter(
                            stoponroute__route=route,
                        ).distance(entity.location).order_by('distance')[0]
                    origin_stop = StopOnRoute.objects.get(route=route,
                                                          entity=closest_origin)
                    
                    if stoponroute.order > origin_stop.order:
                        # now check that this stop comes after our
                        # first stop...
                        closest_stop = stop
                        break
                    
                if closest_stop:
                    break
            
            p_and_r_context = {
                'start': entity,
                'routes': set(routes) & set(sor.route.service_id for sor in closest_stop.stoponroute_set.all()),
                'origin_stop': origin_stop,
                'closest_stop': closest_stop
            }
            start_location = closest_stop
        else:
            # Directions from that point to first stop
            start_location, p_and_r_context = entity, {}
        return start_location, p_and_r_context
    
    def initial_context(self, request, tour, page=None):
        
        context = super(TourView, self).initial_context(request)
        tour = get_object_or_404(Tour, id=tour)
        context.update({
            'tour': tour,
            'stops': StopOnTour.objects.filter(tour=tour)
        })
        
        if page is not None:
            stop = get_object_or_404(StopOnTour, tour=tour, order=page)
            context['stop'] = stop
            
            try:
                context['next_stop'] = StopOnTour.objects.get(tour=tour, order=int(page)+1)
            except StopOnTour.DoesNotExist:
                pass
            
            try:
                context['previous_stop'] = StopOnTour.objects.get(tour=tour, order=int(page)-1)
            except StopOnTour.DoesNotExist:
                pass
        
        else:
            
            try:
                arrival_point = int(request.GET.get('arrival_point'))
            except (ValueError, TypeError):
                arrival_point = None
            arrival_route = request.GET.get('arrival_route')
            
            if arrival_point is not None or arrival_route:
                
                first_stop = tour.stops.all()[0]
                
                if arrival_point is not None:
                
                    start_location, p_and_r_context = self.arrival_point_location(first_stop, arrival_point)
                    context['p_and_r'] = p_and_r_context
                
                elif arrival_route is not None:
                
                    start_location = self.arrival_route_location(first_stop, arrival_route)
                    context['arrival_route'] = arrival_route
                
                if start_location is not None:
                    context['first_directions'] = generate_route(
                        [start_location.location, first_stop.location], 'foot')
                    if 'error' not in context['first_directions']:
                        context['directions_start'] = start_location
                        context['directions_end'] = first_stop
                        context['directions_map'] = Map(
                            (start_location.location[0], start_location.location[1], 'green', ''),
                            [(w['location'][0], w['location'][1], 'red', w['instruction'])
                                for w in context['first_directions']['waypoints']],
                            len(context['first_directions']['waypoints']),
                            None,
                            request.map_width,
                            request.map_height,
                            extra_points=[(first_stop.location[0],
                                           first_stop.location[1],
                                           'red', first_stop.title)],
                            paths=[(context['first_directions']['path'], '#3c3c3c')])
            
            else:
            
                arrival_points = []
                for i, arrival_point in enumerate(getattr(self.conf, 'arrival_points', [])):
                    arrival_points.append((i, get_entity(*arrival_point[0].split(':'))))
                context.update({
                    'arrival_points': arrival_points,
                    'arrival_routes': getattr(self.conf, 'arrival_routes', []),
                    'created': 'created' in request.GET
                })
            
        return context
    
    def handle_GET(self, request, context, tour, page=None):
        
        if 'tours:visited' in request.session:
            request.session['tours:visited'].add(context['tour'].id)
        else:
            request.session['tours:visited'] = set((context['tour'].id,))
        request.session.save()
        
        user_location = request.session.get('geolocation:location')
        if user_location is None and 'previous_stop' in context:
            user_location = context['previous_stop'].entity.routing_point(context['stop'].entity.location).location
        else:
            user_location = Point(user_location)
        
        if 'stop' in context and \
          context['stop'].entity.routing_point(user_location).location is not None and \
          user_location is not None:
            
            entrance = context['stop'].entity.routing_point(user_location)
            
            context['route'] = generate_route(
                [user_location, entrance.location], 'foot')
            
            context['route_map'] = Map(
                (user_location[0], user_location[1], 'green', ''),
                [(w['location'][0], w['location'][1], 'red', w['instruction'])
                    for w in context['route']['waypoints']],
                len(context['route']['waypoints']),
                None,
                request.map_width,
                request.map_height,
                extra_points=[(entrance.location[0],
                               entrance.location[1],
                               'red', entrance.title)],
                paths=[(context['route']['path'], '#3c3c3c')])
        
        return self.render(request, context, 'tours/tour')


class PaperView(TourView):
    
    def handle_GET(self, request, context, tour):
        # Map QuerySet to list
        context['stops'] = list(context['stops'])
        for i, stop in enumerate(context['stops'][1:], start=1):
            stop.directions_to = generate_route([
                context['stops'][i-1].entity.routing_point(stop.entity.location).location,
                stop.entity.routing_point(context['stops'][i-1].entity.location).location],
                'foot')
        return self.render(request, context, 'tours/paper')

