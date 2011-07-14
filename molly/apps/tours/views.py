from django.utils.translation import ugettext_lazy as _

from molly.apps.places import get_entity
from molly.apps.places.models import EntityType
from molly.utils.breadcrumbs import *
from molly.utils.views import BaseView
from molly.wurfl import device_parents
from molly.routing import generate_route

class IndexView(BaseView):
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            _('Tours'),
            lazy_reverse('index'),
        )
    
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
        
        # Now attempt to order entities optimally
        
        # Save back to database
        
        # Add any suggested "passing-by" entities to the context to be presented
        # back to the user
        
        return super(SaveView, self).handle_GET(request, context, entities)

# TODO: need to have an "update view" for the use case of deciding that you
# want to add a new entity

# Todo: paper view

# Todo: podcast view

# Todo: Mobile tour view
