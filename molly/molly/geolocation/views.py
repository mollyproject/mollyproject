import urllib
from datetime import datetime, timedelta

from django.core.urlresolvers import resolve, reverse
from django.http import HttpResponseRedirect, Http404
from django.contrib.gis.geos import Point
from django.conf import settings

from molly.utils.views import BaseView, renderer
from molly.utils.breadcrumbs import *
from molly.utils.http import HttpResponseSeeOther

from molly.osm.utils import fit_to_map

from .forms import LocationUpdateForm
from .utils import geocode, reverse_geocode

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        try:
            parent_view, args, kwargs = resolve(request.REQUEST['return_url'])
            parent_data = parent_view.breadcrumb.data(cls, request, context, *args, **kwargs)
            parent_data = parent_data.parent(cls, request, context)
            
            parent = lambda _1, _2, _3: parent_data
            application = parent_data.application
        except Exception:
            application = 'home'
            parent = lambda _1,_2,_3: type(
                'BC', (), {
                    'application': 'home',
                    'title': 'Back...',
                    'url':staticmethod(lambda:request.REQUEST.get('return_url', reverse('home:index')))
                }
            )
        return Breadcrumb(
            application,
            parent,
            'Update location',
            lazy_reverse('geolocation:index'),
        )

    def initial_context(cls, request):
        data = dict(request.REQUEST.items())
        data['http_method'] = request.method
        return {
            'form': LocationUpdateForm(data, reverse_geocode = lambda lon, lat:reverse_geocode(lon, lat, cls.conf.local_name)),
            'format': request.REQUEST.get('format'),
            'return_url': request.REQUEST.get('return_url', ''),
            'requiring_url': hasattr(request, 'requiring_url'),
        }

    def handle_GET(cls, request, context):
        form = context['form']

        if form.is_valid():
            results = geocode(form.cleaned_data['name'], cls.conf.local_name)

            if results:
                points = [(o['location'][0], o['location'][1], 'red') for o in results]
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
                'results': results,
                'map_url': reverse('osm:generated_map', args=[map_hash]) if map_hash else None,
                'zoom': zoom,
                'zoom_controls': False,
            })

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

        if context.get('return_url'):
            redirect = context['return_url']
        else:
            redirect = None
            
        if context['format'] == 'json':
            return cls.render(request, {
                'name': form.cleaned_data['name'],
                'redirect': redirect,
            }, None)
        else:
            return HttpResponseRedirect(redirect)
            
    @renderer(format="embed", mimetypes=())
    def render_embed(cls, request, context, template_name):
        return cls.render_html(request, context, template_name)

    @renderer(format="html")
    def render_html(cls, request, context, template_name):
        if request.method == 'POST':
            if context.get('return_url'):
                return HttpResponseRedirect(context['return_url'])
            else:
                return HttpResponseRedirect(reverse('core:index'))
        else:
            return super(IndexView, cls).render_html(request, context, template_name)

    def set_location(cls, request, name, location, accuracy, method):
        if isinstance(location, list):
            location = tuple(location)
        
        last_updated = request.session.get('geolocation:updated', datetime(1970, 1, 1))
        try:
            last_location = Point(request.session['geolocation:location'], srid=4326)
            distance_moved = last_location.transform(settings.SRID, clone=True).distance(Point(location, srid=4326).transform(settings.SRID, clone=True))
        except KeyError:
            distance_moved = float('inf')
            
        if method in ('other', 'manual', 'geocoded') or \
           not 'geolocation:location' in request.session or \
           (last_updated > datetime.utcnow() - timedelta(seconds=3600) and distance_moved > 250):
            cls.add_to_history(request, name, location, accuracy, method)

        request.session['geolocation:location'] = location
        request.session['geolocation:updated'] = datetime.utcnow()
        request.session['geolocation:name'] = name
        request.session['geolocation:method'] = method
        request.session['geolocation:accuracy'] = accuracy
    
    def add_to_history(cls, request, name, location, accuracy, method):
        if not 'geolocation:history' in request.session:
            request.session['geolocation:history'] = []
        request.session['geolocation:history'].insert(0, {
            'location': location,
            'updated': datetime.utcnow(),
            'name': name,
            'method': method,
            'accuracy': accuracy,
        })

        # Chop off the last element if the history is now larger than the
        # maximum allowed length.        
        history_size = getattr(cls.conf, 'history_size', 5)
        request.session['geolocation:history'][history_size:] = []
        
        request.session.modified = True
        
class ClearHistoryView(BaseView):
    def handle_POST(cls, request, context):
        for key in request.session:
            if key.startswith('geolocation:'):
                del request.session[key]
        return HttpResponseSeeOther(request.GET.get('redirect_to', reverse('home:index')))

class LocationRequiredView(BaseView):
    def is_location_required(cls, request, *args, **kwargs):
        return True

    def __new__(cls, request, *args, **kwargs):
        if not cls.is_location_required(request, *args, **kwargs) or request.session.get('geolocation:location'):
            return super(LocationRequiredView, cls).__new__(cls, request, *args, **kwargs)
        else:
            return HttpResponseSeeOther('%s?%s' % (
                reverse('geolocation:index'),
                urllib.urlencode({'return_url': request.get_full_path()}),
            ))

