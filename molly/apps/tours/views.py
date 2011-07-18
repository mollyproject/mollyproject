from django.core.urlresolvers import reverse
from django.contrib.gis.measure import D
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from molly.apps.places import get_entity
from molly.apps.places.models import Entity, EntityType
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


# Todo: paper view

# Todo: podcast view

# Todo: Mobile tour view
