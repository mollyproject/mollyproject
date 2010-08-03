import urllib
from datetime import datetime, timedelta

from django.core.urlresolvers import resolve, reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseBadRequest
from django.contrib.gis.geos import Point
from django.conf import settings

from molly.utils.views import BaseView, renderer
from molly.utils.breadcrumbs import *
from molly.utils.http import HttpResponseSeeOther, update_url

from molly.osm.utils import fit_to_map

from .forms import LocationUpdateForm
from .utils import geocode, reverse_geocode


class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        if not request.REQUEST.get('return_url'):
            return Breadcrumb(
                cls.conf.local_name,
                None,
                'Update location',
                lazy_reverse('geolocation:index'),
            )

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
        return {
            'form': LocationUpdateForm(data),
            'format': request.REQUEST.get('format'),
            'return_url': request.REQUEST.get('return_url', ''),
            'requiring_url': hasattr(request, 'requiring_url'),
        }

    def handle_GET(cls, request, context):
        if context['format'] == 'embed':
            return cls.render(request, context, 'geolocation/update_location_embed')
        else:
            if request.session.get('geolocation:location') and context.get('return_url'):
                print repr(context.get('return_url'))
                return HttpResponseSeeOther(context.get('return_url'))
            return cls.render(request, context, 'geolocation/update_location')

    def handle_POST(cls, request, context):
        form = context['form']

        if form.is_valid():
            context['return_url'] = update_url(context['return_url'], {'location_error': None}, None)
            return cls.handle_set_location(request, context)
        else:
            if context['format'] == 'json':
                context = {
                    'error': form.errors.popitem()[1].pop(),
                }
                return cls.render(request, context, None)
            else:
                return_url = update_url(
                    context['return_url'],
                    {'location_error': form.errors.popitem()[1].pop()},
                    'location-update',
                )
                return HttpResponseSeeOther(return_url)

    def handle_set_location(cls, request, context):
        form = context['form']

        if form.is_valid():
            cls.set_location(request,
                             form.cleaned_data['name'],
                             form.cleaned_data['location'],
                             form.cleaned_data['accuracy'],
                             form.cleaned_data['method'])

        if context.get('return_url').startswith('/'):
            redirect = context['return_url']
        elif context['format'] == 'json':
            redirect = None
        else:
            redirect = reverse('home:index')

        if context['format'] == 'json':
            return cls.render(request, {
                'name': form.cleaned_data['name'],
                'redirect': redirect,
                'accuracy': form.cleaned_data['accuracy'],
                'longitude': form.cleaned_data['location'][0],
                'latitude': form.cleaned_data['location'][1],
                'history': request.session.get('geolocation:history', ())[1:],
            }, None)
        elif context['format'] == 'embed':
            response = HttpResponse('')
            response['X-Embed-Redirect'] = redirect
            response['X-Embed-Location-Name'] = form.cleaned_data['name']
            return response
        else:
            return HttpResponseSeeOther(redirect)

    @renderer(format="embed", mimetypes=())
    def render_embed(cls, request, context, template_name):
        response = cls.render_html(request, context, template_name)
        response['X-Embed'] = 'True'
        return response

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

        request.session['geolocation:history'] = [e for i, e in enumerate(request.session['geolocation:history']) if e['name'] != name or i == 0]

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

