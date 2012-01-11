import re
from operator import itemgetter

from django.contrib.gis.geos import Point
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.http import Http404
from django.template.defaultfilters import capfirst

from molly.conf import app_by_application_name

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.favourites import get_favourites

from molly.apps.places import get_entity, bus_route_sorter
from molly.apps.places.models import Entity, EntityType, Route

class TransportView(BaseView):
    
    def record_page(self, request, page):
        request.session['transport:last'] = page
        request.session.save()
    
    def augment_metadata(self, entities, **kwargs):
        # Get any real-time information for all the places we're about to display
        places_conf = app_by_application_name('molly.apps.places')
        for provider in reversed(places_conf.providers):
            provider.augment_metadata(entities, **kwargs)
    
    def initial_context(self, request):
        
        context = super(TransportView, self).initial_context(request)
        
        # Get our location for location sorting
        location = request.session.get('geolocation:location')
        if location:
            location = Point(location, srid=4326)
        
        context['location'] = location
        
        # Determine what's enabled so we can show it in base.html
        context['train_station'] = hasattr(self.conf, 'train_station')
        context['travel_alerts'] = getattr(self.conf, 'travel_alerts', False)
        context['park_and_rides'] = hasattr(self.conf, 'park_and_rides')
        context['public_transport'] = dict((key, True)
                                    for key in getattr(self.conf, 'nearby', {}))
        
        return context


class IndexView(BaseView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            _('Transport'),
            lazy_reverse('%s:index' % self.conf.local_name),
        )
    
    def handle_GET(self, request, context):
        last_part = request.session.get('transport:last',
                                        getattr(self.conf, 'default_page', 'bus'))
        if last_part in ('rail', 'park-and-ride', 'travel-news'):
            redirect_to = reverse('transport:%s' % last_part)
        else:
            redirect_to = reverse('transport:public-transport', args=[last_part])
        return self.redirect(redirect_to, request)


class RailView(TransportView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            _('Rail departures') if context['board'] == 'departures' else _('Rail arrivals'),
            lazy_reverse('%s:rail' % self.conf.local_name),
        )
    
    def initial_context(self, request):
        
        context = super(RailView, self).initial_context(request)
        
        if context['train_station']:
            if getattr(self.conf, 'train_station_nearest', False) \
              and context['location']:
                et = EntityType.objects.get(slug='rail-station')
                entity = et.entities_completion.filter(location__isnull=False)
                entity = entity.distance(context['location']).order_by('distance')[0]
            else:
                scheme, value = self.conf.train_station.split(':')
                entity = get_entity(scheme, value)
                
            context['entity'] = entity
        else:
            raise Http404()
            
        places_conf = app_by_application_name('molly.apps.places')
        attributions = [provider._ATTRIBUTION for provider in places_conf.providers
                      if hasattr(provider, '_ATTRIBUTION')]
        context['attributions'] = attributions

        context['board'] = request.GET.get('board', 'departures')

        self.augment_metadata([entity], board=context['board'])
        
        return context
    
    def handle_GET(self, request, context):
        self.record_page(request, 'rail')
        return self.render(request, context, 'transport/rail')


class TravelNewsView(TransportView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            _('Travel alerts'),
            lazy_reverse('%s:travel-news' % self.conf.local_name),
        )
    
    def initial_context(self, request):
        
        context = super(TravelNewsView, self).initial_context(request)
            
        if context['travel_alerts']:
            es = Entity.objects.filter(primary_type__slug='travel-alert')
            if context['location']:
                es = es.filter(location__isnull=False).distance(location).order_by('distance')
            else:
                es = es.order_by('title')
            context['travel_alerts'] = es
        else:
            raise Http404()
        
        return context
    
    def handle_GET(self, request, context):
        self.record_page(request, 'travel-news')
        return self.render(request, context, 'transport/travel_news')


class ParkAndRideView(TransportView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            _('Park and Ride'),
            lazy_reverse('%s:park-and-ride' % self.conf.local_name),
        )
    
    def initial_context(self, request):
        
        context = super(ParkAndRideView, self).initial_context(request)
        
        # If park and ride variable is set, then include those too:
        if context['park_and_rides']:
            park_and_rides = []
            for park_and_ride in self.conf.park_and_rides:
                scheme, value = park_and_ride.split(':')
                entity = get_entity(scheme, value)
                park_and_rides.append(entity)
            context['park_and_rides'] = park_and_rides
        else:
            raise Http404()

        self.augment_metadata(park_and_rides)
        return context
    
    def handle_GET(self, request, context):
        self.record_page(request, 'park-and-ride')
        return self.render(request, context, 'transport/park_and_ride')


class PublicTransportView(TransportView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context, key):
        type_slug, count = self.conf.nearby[key]
        et = EntityType.objects.get(slug=type_slug)
        return Breadcrumb(
            self.conf.local_name,
            None,
            capfirst(et.verbose_name_plural),
            lazy_reverse('%s:public-transport' % self.conf.local_name,
                         kwargs={'key': key}),
        )
    
    def initial_context(self, request, key):
        
        context = super(PublicTransportView, self).initial_context(request)
        
        location = context['location']
        selected_routes = request.GET.getlist('route')
        
        if key not in getattr(self.conf, 'nearby', {}):
            raise Http404()
        
        # If service status provider is set, then include those too:
        if hasattr(self.conf, '%s_status_provider' % key):
            provider = getattr(self.conf, '%s_status_provider' % key)
            context['line_status'] = provider.get_status()
        
        type_slug, count = self.conf.nearby[key]
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
        
        else:
            
            if location:
                es = et.entities_completion.filter(location__isnull=False)
                es = es.distance(location).order_by('distance')[:count]
            else:
                es = []
        
        for e in (e for e in es if hasattr(e, 'distance')):
            distance, e.bearing = e.get_distance_and_bearing_from(location)
        
        self.augment_metadata(es, routes=selected_routes)
        
        for e in (e for e in favourites if hasattr(e, 'distance')):
            distance, e.bearing = e.get_distance_and_bearing_from(location)
        self.augment_metadata(favourites)
        
        context.update({
            'pageslug': key,
            'type': et,
            'entities': es,
            'favourites': favourites
        })
        
        # Only show routes which serve this type of thing
        routes = Route.objects.filter(stoponroute__entity__all_types_completion=et).distinct()
        route_ids = routes.values_list('service_id').distinct()
        
        context['route_ids'] = sorted(map(itemgetter(0), route_ids), key=bus_route_sorter)
        context['selected_routes'] = selected_routes
        
        return context
    
    def handle_GET(self, request, context, key):
        return self.render(request, context, 'transport/public_transport')


class RoutesView(TransportView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context, key):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('transport:public-transport', key=key),
            _('Routes'),
            lazy_reverse('%s:route' % self.conf.local_name),
        )
    
    def initial_context(self, request, key):
        
        context = super(RoutesView, self).initial_context(request)
        
        type_slug, count = self.conf.nearby[key]
        et = EntityType.objects.get(slug=type_slug)
        
        if key not in getattr(self.conf, 'nearby', {}):
            raise Http404()
        
        location = context['location']
        
        # Only show routes which serve this type of thing
        routes = Route.objects.filter(stoponroute__entity__all_types_completion=et).distinct()
        
        if location:
            routes = list(routes)
            for route in routes:
                route.nearest = Entity.objects.filter(route=route).distance(location).order_by('distance')[0]
                route.nearest_distance, route.nearest_bearing = route.nearest.get_distance_and_bearing_from(location)
        
        context['routes'] = sorted(routes, key=lambda x: bus_route_sorter(x.service_id))
        
        return context
    
    def handle_GET(self, request, context, key):
        return self.render(request, context, 'transport/routes')
    
