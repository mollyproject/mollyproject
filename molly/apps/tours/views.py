from django.core.urlresolvers import reverse
from django.contrib.gis.measure import D
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
        
        if 'tours:visited' in request.session:
            context.update({
                'tours': Tour.objects.filter(id__in=request.session['tours:visited'])
            })
        
        return context
    
    def handle_GET(self, request, context):
        return self.render(request, context, 'tours/index')

class CreateView(BaseView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context, entities):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            _('Create a tour'),
            lazy_reverse('create'),
        )
    
    def initial_context(self, request, entities):
        context = super(CreateView, self).initial_context(request)
        
        context.update({
            'entities': [],
            'attractions': dict((et, et.entity_set.filter(location__isnull=False))
                for et in EntityType.objects.filter(slug__in=self.conf.attraction_types))
        })
        
        for entity in entities.split('/'):
            try:
                scheme, value = entity.split(':')
            except ValueError:
                continue
            context['entities'].append(get_entity(scheme, value))
        
        return context
    
    def handle_GET(self, request, context, entities):
        
        if 'generic_web_browser' in device_parents[request.browser.devid]:
            # Desktop
            return self.render(request, context, 'tours/create_desktop')
        else:
            return self.render(request, context, 'tours/create')


class SaveView(CreateView):
    
    def handle_GET(self, request, context, entities):
        
        if len(context['entities']) < 2:
            # Need at least 2 entities to be a tour
            return self.bad_request(request)
        
        # Now attempt to order entities optimally
        if len(context['entities']) > 2 and len(context['entities']) <= 10:
            context['entities'] = optimise_points([(entity, entity.location) for entity in context['entities']])
            context['optimised_entities'] = True
        
        # Save back to database
        tour = Tour.objects.create()
        for i, entity in enumerate(context['entities']):
            StopOnTour.objects.create(entity=entity, tour=tour, order=i)
        
        # Add any suggested "passing-by" entities to the context to be presented
        # back to the user
        if hasattr(self.conf, 'suggested_entities'):
            route = generate_route([e.location for e in context['entities']], 'foot')
            suggestion_filter = Q()
            for sv in self.conf.suggested_entities:
                scheme, value = sv.split(':')
                suggestion_filter |= Q(_identifiers__scheme=scheme,
                                       _identifiers__value=value)
            context['suggestions'] = Entity.objects.filter(
                suggestion_filter,
                location__distance_lt=(route['path'],
                        D(m=getattr(self.conf, 'suggestion_distance', 100))))
        
        context['tour'] = tour
        
        return super(SaveView, self).handle_GET(request, context, entities)

class PdfView(BaseView):
    pass

class PodcastView(BaseView):
    pass

class TourView(BaseView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context, tour, page=None):
        
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            context['stop'].entity.title if page else _('Tour'),
            lazy_reverse('tour', args=(context['tour'].pk, page)),
        )
    
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
            
            arrival_point = request.GET.get('arrival_point')
            if arrival_point:
                first_stop = tour.stops.all()[0]
                sv, p_and_r, routes = self.conf.arrival_points[int(arrival_point)]
                entity = get_entity(*sv.split(':'))
                if p_and_r:
                    # Get closest bus stop to first stop on route, then plot
                    # route
                    closest_stop = Entity.objects.filter(
                            stoponroute__route__service_id__in=routes,
                        ).distance(first_stop.location).order_by('distance')[0]
                    context['p_and_r'] = {
                        'start': entity,
                        'routes': set(routes) & set(sor.route.service_id for sor in closest_stop.stoponroute_set.all()),
                        'closest_stop': closest_stop
                    }
                    start_location = closest_stop
                else:
                    # Directions from that point to first stop
                    start_location = entity
                
                context['first_directions'] = generate_route(
                    [start_location.location, first_stop.location], 'foot')
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
            user_location = context['previous_stop'].entity.location
        
        if 'stop' in context and \
          context['stop'].entity.location is not None and \
          user_location is not None:
            
            context['route'] = generate_route(
                [user_location, context['stop'].entity.location], 'foot')
            
            context['route_map'] = Map(
                (user_location[0], user_location[1], 'green', ''),
                [(w['location'][0], w['location'][1], 'red', w['instruction'])
                    for w in context['route']['waypoints']],
                len(context['route']['waypoints']),
                None,
                request.map_width,
                request.map_height,
                extra_points=[(context['stop'].entity.location[0],
                               context['stop'].entity.location[1],
                               'red', context['stop'].entity.title)],
                paths=[(context['route']['path'], '#3c3c3c')])
        
        return self.render(request, context, 'tours/tour')

