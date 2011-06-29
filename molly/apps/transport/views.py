import re
from operator import itemgetter

from django.contrib.gis.geos import Point
from django.utils.translation import ugettext as _

from molly.conf import app_by_application_name

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.favourites import get_favourites

from molly.apps.places import get_entity
from molly.apps.places.models import Entity, EntityType, Route

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            _('Transport'),
            lazy_reverse('%s:index' % self.conf.local_name),
        )
    
    def initial_context(self, request):
        
        # Get our location for location sorting
        location = request.session.get('geolocation:location')
        if location:
            location = Point(location, srid=4326)
        
        selected_routes = request.GET.getlist('route')
        
        context, entities = {'location':location}, set()
        
        # If train station is set on config, then include that
        if hasattr(self.conf, 'train_station'):
            if getattr(self.conf, 'train_station_nearest', False) and location:
                et = EntityType.objects.get(slug='rail-station')
                entity = et.entities_completion.filter(location__isnull=False).distance(location).order_by('distance')[0]
            else:
                scheme, value = self.conf.train_station.split(':')
                entity = get_entity(scheme, value)
            entities.add(entity)
            context['train_station'] = entity
        
        # If park and ride variable is set, then include those too:
        if hasattr(self.conf, 'park_and_rides'):
            park_and_rides = []
            for park_and_ride in self.conf.park_and_rides:
                scheme, value = park_and_ride.split(':')
                entity = get_entity(scheme, value)
                park_and_rides.append(entity)
                entities.add(entity)
            context['park_and_rides'] = park_and_rides
        
        # If service status provider is set, then include those too:
        if hasattr(self.conf, 'transit_status_provider'):
            context['transit_status'] = self.conf.transit_status_provider.get_status()
        
        context['nearby'] = {}
        for context_key in getattr(self.conf, 'nearby', {}):
            type_slug, count = self.conf.nearby[context_key]
            et = EntityType.objects.get(slug=type_slug)
            
            favourites = filter(
                lambda e: e is not None and et in e.all_types_completion.all(),
                [f.metadata.get('entity') for f in get_favourites(request)])
            
            if selected_routes:
                
                if location:
                    es = et.entities_completion.filter(
                        location__isnull=False, route__service_id__in=selected_routes)
                    es = es.distinct().distance(location).order_by('distance')[:count]
                else:
                    es = []
                results_type = 'Nearby'
                
            elif request.GET.get(context_key) == 'nearby':
                
                if location:
                    es = et.entities_completion.filter(location__isnull=False)
                    es = es.distance(location).order_by('distance')[:count]
                else:
                    es = []
                results_type = 'Nearby'
                
            elif request.GET.get(context_key) == 'favourites':
                
                es = favourites    
                results_type = 'Favourite'
                
            else:
                
                if len(favourites) == 0:
                    if location:
                        es = et.entities_completion.filter(location__isnull=False)
                        es = es.distance(location).order_by('distance')[:count]
                    else:
                        es = []
                else:
                    es = favourites
                
                results_type = 'Favourite' if len(favourites) > 0 else 'Nearby'
            
            for e in (e for e in es if hasattr(e, 'distance')):
                distance, e.bearing = e.get_distance_and_bearing_from(location)
            
            entities |= set(es)
            context['nearby'][context_key] = {
                'type': et,
                'entities': es,
                'results_type': results_type,
            }
            
        if getattr(self.conf, 'travel_alerts', False):
            es = Entity.objects.filter(primary_type__slug='travel-alert')
            if location:
                es = es.filter(location__isnull=False).distance(location).order_by('distance')
            else:
                es = es.order_by('title')
            entities |= set(es)
            context['travel_alerts'] = es
        
        # Get any real-time information for all the places we're about to display
        places_conf = app_by_application_name('molly.apps.places')
        for provider in reversed(places_conf.providers):
            provider.augment_metadata(entities,
                                      board=request.GET.get('board', 'departures'),
                                      routes=selected_routes)
        
        context['board'] = request.GET.get('board', 'departures')
        routes = Route.objects.values_list('service_id').distinct()
        
        # Now sort routes numerically
        def bus_route_sorter(route):
            start_nums = re.match('([0-9]+)([A-Z]?)', route)
            letter_nums = re.match('([A-Z]+)([0-9]+)([A-Z]?)', route)
            if start_nums:
                return int(start_nums.group(1)), start_nums.group(2)
            elif letter_nums:
                return letter_nums.group(1), int(letter_nums.group(2)), letter_nums.group(2)
            else:
                return route
        
        context['routes'] = sorted(map(itemgetter(0), routes), key=bus_route_sorter)
        context['selectedroutes'] = selected_routes
        
        
        return context
    
    def handle_GET(self, request, context):
        return self.render(request, context, 'transport/index')

