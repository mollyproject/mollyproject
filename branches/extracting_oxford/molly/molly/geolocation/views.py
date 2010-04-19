from datetime import datetime

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from molly.osm.utils import fit_to_map

from .forms import LocationUpdateForm

class IndexView(BaseView):
    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context):
        return cls.render(request, context, 'geolocation/index')

class LocationUpdateView(BaseView):
    breadcrumb = NullBreadcrumb

    def initial_context(cls, request):
        data = dict(request.REQUEST.items())
        data['http_method'] = request.method
        return {
            'form': LocationUpdateForm(data, reverse_geocode = cls.conf.providers[0].reverse_geocode),
            'format': request.REQUEST.get('format'),
            'return_url': request.REQUEST.get('return_url', ''),
            'requiring_url': hasattr(request, 'requiring_url'),
        }

    def handle_GET(cls, request, context):
        form = context['form']

        if form.is_valid():
            placemarks = []
            for provider in cls.conf.providers:
                placemarks += provider.geocode(form.cleaned_data['name'])

            if placemarks:
                points = [(o['location'][0], o['location'][1], 'red') for o in placemarks]
                print "POINTS", points
                map_hash, (new_points, zoom) = fit_to_map(
                    None,
                    points = points,
                    min_points = len(points),
                    zoom = None if len(points)>1 else 15,
                    width = request.map_width,
                    height = request.map_height,
                )
            else:
                map_hash, zoom = None, None
            context.update({
                'placemarks': placemarks,
                'map_url': reverse('osm:generated_map', args=[map_hash]) if map_hash else None,
                'zoom': zoom,
                'zoom_controls': False,
            })
#        else:
#            context['placemarks'] = []

        if context['format'] == 'json':
            del context['form']
            del context['format']
            del context['breadcrumbs']
            return cls.json_response(context)
        elif context['format'] == 'embed':
            if form.is_valid():
                return cls.render(request, context, 'geolocation/update_location_confirm')
            else:
                return cls.render(request, context, 'geolocation/update_location_embed')
        else:
            return cls.render(request, context, 'geolocation/update_location')


    def handle_POST(cls, request, context):
        form = context['form']

        if form.is_valid():
            cls.set_location(request,
                             form.cleaned_data['name'],
                             form.cleaned_data['location'],
                             form.cleaned_data['accuracy'],
                             form.cleaned_data['method'])

        return cls.render(request, context, None)

    def render_html(cls, request, context, template_name):
        if request.method == 'POST':
            if context.get('return_url'):
                return HttpResponseRedirect(context['return_url'])
            else:
                return HttpResponseRedirect(reverse('core:index'))
        else:
            super(LocationUpdateView, self).render_html(request, context, template_name)

    def set_location(cls, request, name, location, accuracy, method):
        if isinstance(location, list):
            location = tuple(location)

        request.session['geolocation:location'] = location
        print "setting", location
        request.session['geolocation:updated'] = datetime.now()
        request.session['geolocation:name'] = name
        request.session['geolocation:method'] = method
        request.session['geolocation:accuracy'] = accuracy

class LocationRequiredView(BaseView):
    def is_location_required(cls, request, *args, **kwargs):
        return True

    def __new__(cls, request, *args, **kwargs):
        if not cls.is_location_required(request, *args, **kwargs) or request.session.get('geolocation:location'):
            return super(LocationRequiredView, cls).__new__(cls, request, *args, **kwargs)
        else:
            request.GET = dict(request.GET.items())
            request.GET['return_url'] = request.path
            request.requiring_location = True
            return LocationUpdateView(request)

