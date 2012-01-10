import urllib, random
from datetime import datetime, timedelta
from urlparse import urlparse

from django.core.urlresolvers import resolve, reverse
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.contrib.gis.geos import Point
from django.conf import settings
from django.utils.translation import ugettext as _

from molly.utils.views import BaseView, renderer
from molly.utils.breadcrumbs import *
from molly.utils.http import update_url
from molly.utils.templatetags.molly_utils import humanise_distance
from molly.utils import haversine

from molly.geolocation.forms import LocationUpdateForm
from molly.geolocation import geocode, reverse_geocode

class GeolocationView(BaseView):
    """
    Deals with setting location using POST requests (either forms or AJAX)
    """
    
    def initial_context(self, request):
        data = dict(request.REQUEST.items())
        return {
            'form': LocationUpdateForm(data),
            'format': request.REQUEST.get('format'),
            'return_url': request.REQUEST.get('return_url', ''),
            'requiring_url': hasattr(request, 'requiring_url'),
        }

    def set_location(self, request, name, location, accuracy, method, with_history=False):
        request.session['geolocation:location'] = location
        request.session['geolocation:updated'] = datetime.utcnow()
        request.session['geolocation:name'] = name
        request.session['geolocation:method'] = method
        request.session['geolocation:accuracy'] = accuracy

        if not with_history:
            return

        if isinstance(location, list):
            location = tuple(location)
        last_updated = request.session.get('geolocation:updated', datetime(1970, 1, 1))
        try:
            last_location = Point(request.session['geolocation:location'])
            distance_moved = haversine(last_location, Point(location))
        except KeyError:
            distance_moved = float('inf')

        if method in ('other', 'manual', 'geocoded', 'html5request') or \
           not 'geolocation:location' in request.session or \
           (last_updated > datetime.utcnow() - timedelta(seconds=3600) and distance_moved > 250):
            self.add_to_history(request, name, location, accuracy, method)

    def add_to_history(self, request, name, location, accuracy, method):
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
        history_size = getattr(self.conf, 'history_size', 5)
        request.session['geolocation:history'][history_size:] = []

        request.session.modified = True

    def handle_set_location(self, request, context):
        form = context['form']

        if form.is_valid():
            self.set_location(request,
                             form.cleaned_data['name'],
                             form.cleaned_data['location'],
                             form.cleaned_data['accuracy'],
                             form.cleaned_data['method'],
                             True)

        if context.get('return_url').startswith('/'):
            redirect = context['return_url']
        elif context['format'] == 'json':
            redirect = None
        else:
            redirect = reverse('home:index')

    @renderer(format="embed", mimetypes=())
    def render_embed(self, request, context, template_name):
        response = self.render_html(request, context, template_name)
        response['X-Embed'] = 'True'
        return response

    def get_location_response(self, request, context, form=None):
        if context.get('return_url').startswith('/'):
            redirect = context['return_url']
        else:
            redirect = reverse('home:index')
        if context['format'] == 'json':
            return self.render(request, {
                'name': request.session['geolocation:name'],
                'redirect': redirect,
                'accuracy': humanise_distance(request.session['geolocation:accuracy']),
                'longitude': request.session['geolocation:location'][0],
                'latitude': request.session['geolocation:location'][1],
                'history': request.session.get('geolocation:history', ()),
                'alternatives': form.cleaned_data.get('alternatives') if form else None,
                'favourites': [dict(favourite.items() + [('id', id)]) for id, favourite in request.session.get('geolocation:favourites', {}).items()],
            }, None)
        elif context['format'] == 'embed':
            response = HttpResponse('')
            response['X-Embed-Redirect'] = redirect
            response['X-Embed-Location-Name'] = form.cleaned_data['name']
            return response
        else:
            alternatives = form.cleaned_data.get('alternatives') if form else None
            if alternatives != None and len(alternatives) > 0:
                # Not doing AJAX update, so show the form allowing users to
                # choose a location from alternatives before returning to their
                # original screen
                context.update({
                    'geolocation_alternatives': form.cleaned_data.get('alternatives')
                })
                return self.handle_GET(request, context)
            else:
                return self.redirect(redirect, request, 'seeother')

class IndexView(GeolocationView):
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        if not request.REQUEST.get('return_url'):
            return Breadcrumb(
                self.conf.local_name,
                None,
                _('Update location'),
                lazy_reverse('geolocation:index'),
            )

        try:
            return_url = urlparse(request.REQUEST['return_url']).path
            parent_view, args, kwargs = resolve(return_url)
            parent_data = parent_view.breadcrumb.data(self, request, context, *args, **kwargs)
            parent_data = parent_data.parent(self, parent_view.conf.local_name, request, context)

            parent = lambda _1, _2, _3, _4: parent_data
            application = parent_data.application
        except Exception:
            application = 'home'
            parent = lambda _1,_2,_3, _4: type(
                'BC', (), {
                    'application': 'home',
                    'title': 'Back...',
                    'url':staticmethod(lambda _:request.REQUEST.get('return_url', reverse('home:index')))
                }
            )
        return Breadcrumb(
            application,
            parent,
            _('Update location'),
            lazy_reverse('index'),
        )

    def handle_GET(self, request, context):
        if context['format'] == 'embed':
            return self.render(request, context, 'geolocation/update_location_embed')
        else:
            if request.session.get('geolocation:location') \
              and context.get('return_url') \
              and not request.REQUEST.get('update', False) \
              and not 'geolocation_alternatives' in context:
                return self.redirect(context.get('return_url'),
                                     request, 'seeother')
            return self.render(request, context, 'geolocation/update_location')

    def handle_POST(self, request, context):
        form = context['form']

        if form.is_valid():
            context['return_url'] = update_url(context['return_url'], {'location_error': None}, None)
            self.handle_set_location(request, context)
            return self.get_location_response(request, context, form)
        else:
            if context['format'] == 'json':
                context = {
                    'error': form.errors.popitem()[1].pop(),
                }
                return self.render(request, context, None)
            else:
                return_url = update_url(
                    context['return_url'],
                    {'location_error': form.errors.popitem()[1].pop()},
                    'location-update',
                )
                return self.redirect(return_url, request, 'seeother')

class FavouritesView(GeolocationView):
    breadcrumb = NullBreadcrumb

    actions = frozenset(['add', 'remove', 'set'])

    def new_id(self, request):
        while True:
            id = ''.join(random.choice('0123456789abcdef') for i in range(8))
            if id in request.session['geolocation:favourites']:
                continue
            return id

    def handle_POST(self, request, context):
        if not 'geolocation:favourites' in request.session:
            request.session['geolocation:favourites'] = {}

        action = request.POST.get('action')

        if action not in self.actions:
            return HttpResponseBadRequest()

        handler = getattr(self, 'do_%s' % action)

        try:
            handler(request, context)
        except (ValueError, KeyError):
            return HttpResponseBadRequest()

        return self.get_location_response(request, context)

    def do_add(self, request, context):
        id = self.new_id(request)

        if any(f['name'] == request.POST['name'] for f in request.session['geolocation:favourites'].values()):
            return

        request.session['geolocation:favourites'][id] = {
            'name': request.POST['name'],
            'location': (float(request.POST['longitude']), float(request.POST['latitude'])),
            'accuracy': float(request.POST['accuracy']),
        }
        request.session.modified = True

    def do_remove(self, request, context):
        request.session['geolocation:favourites'].pop(request.POST['id'], None)
        request.session.modified = True

    def do_set(self, request, context):
        loc = request.session['geolocation:favourites'][request.POST['id']]
        if context['form'].is_valid():
            self.handle_set_location(request, context)
        else:
            raise ValueError

class ClearHistoryView(GeolocationView):
    breadcrumb = NullBreadcrumb

    def handle_POST(self, request, context):
        keys_to_delete = set()
        for key in request.session._session:
            if key.startswith('geolocation:history'):
                keys_to_delete.add(key)
        for key in keys_to_delete:
            del request.session[key]
        request.session.modified = True
        context['return_url'] = request.POST.get('return_url', reverse('home:index'))
        return self.get_location_response(request, context)

class LocationRequiredView(BaseView):
    def is_location_required(self, request, *args, **kwargs):
        return True

    def __call__(self, request, *args, **kwargs):
        if not self.is_location_required(request, *args, **kwargs) or hasattr(request, 'user_location'):
            return super(LocationRequiredView, self).__call__(request, *args, **kwargs)
        else:
            return self.redirect('%s?%s' % (
                reverse('geolocation:index'),
                urllib.urlencode({'return_url': request.get_full_path()}),
            ), request, 'seeother')

