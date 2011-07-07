from molly.apps.places import get_entity
from molly.apps.places.models import EntityType
from molly.utils.views import BaseView
from molly.routing import generate_route

class TourView(BaseView):
    
    def handle_GET(self, request, context, entities):
        
        context = {
            'entities': [],
            'attractions': dict((et, et.entity_set.all()) for et in EntityType.objects.filter(slug__in=self.conf.attraction_types))
        }
        
        for entity in entities.split('/'):
            try:
                scheme, value = entity.split(':')
            except ValueError:
                continue
            context['entities'].append(get_entity(scheme, value))
        
        for i in range(len(context['entities']) - 1):
            entity = context['entities'][i]
            next_entity = context['entities'][i+1]
            if not entity.location or not next_entity.location:
                continue
            entity.directions_to_next = generate_route([entity.location, next_entity.location], 'foot')
        
        return self.render(request, context, 'tours/tour')