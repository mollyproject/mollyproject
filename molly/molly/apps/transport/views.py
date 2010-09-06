from django.contrib.gis.geos import Point

from molly.conf import app_by_application_name

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

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
            type_slug, count, without_location = cls.conf.nearby[context_key]
            et = EntityType.objects.get(slug=type_slug)
            if location:
                es = et.entities_completion.filter(location__isnull=False).distance(location).order_by('distance')[:count]
            elif without_location:
                es = et.entities_completion.filter(location__isnull=False).order_by('title')[:count]
            else:
                continue
            entities |= set(es)
            context[context_key] = {
                'type': et,
                'entities': es,
            }
                
        
        # Get any real-time information for all the places we're about to display
        places_conf = app_by_application_name('molly.apps.places')
        for provider in reversed(places_conf.providers):
            provider.augment_metadata(entities)
        
        return context
    
    def handle_GET(cls, request, context):
        return cls.render(request, context, 'transport/index')