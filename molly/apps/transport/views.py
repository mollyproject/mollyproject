from django.contrib.gis.geos import Point

from molly.conf import app_by_application_name

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.favourites import get_favourites

from molly.apps.places.models import Entity, EntityType

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            cls.conf.local_name,
            None,
            'Transport',
            lazy_reverse('%s:index' % cls.conf.local_name),
        )
    
    def initial_context(cls, request):
        location = request.session.get('geolocation:location')
        if location:
            location = Point(location, srid=4326)
        
        context, entities = {'location':location}, set()
        
        if cls.conf.train_station:
            scheme, value = cls.conf.train_station.split(':')
            entity = Entity.objects.get(_identifiers__scheme=scheme, _identifiers__value=value)
            entities.add(entity)
            context['train_station'] = entity
            
        for context_key in getattr(cls.conf, 'nearby', {}):
            type_slug, count, without_location, fav_override = cls.conf.nearby[context_key]
            et = EntityType.objects.get(slug=type_slug)
            if fav_override:
                favourites = filter(lambda e: e is not None and et in e.all_types_completion.all(), [f['metadata'].get('entity') for f in get_favourites(request)])
            
            if not fav_override or len(favourites) == 0:
                if without_location:
                    es = et.entities_completion.order_by('title')[:count]
                elif location:
                    es = et.entities_completion.filter(location__isnull=False).distance(location).order_by('distance')[:count]
                else:
                    context[context_key] = {
                        'results_type': 'Nearby'
                    }
                    continue
            else:
                es = favourites
            
            if context_key == 'park_and_rides' and getattr(cls.conf, 'park_and_ride_sort', None) is not None:
                sorted_es = []
                for key, id in [s.split(':') for s in cls.conf.park_and_ride_sort]:
                    for e in es:
                        if id in e.identifiers[key]:
                            sorted_es.append(e)
                            continue
                es = sorted_es
            
            entities |= set(es)
            context[context_key] = {
                'type': et,
                'entities': es,
                'results_type': 'Favourite' if fav_override and len(favourites) > 0 else 'Nearby'
            }
            
        if getattr(cls.conf, 'travel_alerts', False):
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
            provider.augment_metadata(entities)
        
        return context
    
    def handle_GET(cls, request, context):
        context.update({
            'reload_after_location_update': True,
        })
        return cls.render(request, context, 'transport/index')