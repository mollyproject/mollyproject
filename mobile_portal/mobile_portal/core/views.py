# Create your views here.
from datetime import datetime, timedelta
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.conf import settings
from django.core.management import call_command
from django.template import loader, Context, RequestContext
from mobile_portal.core.renderers import mobile_render
from mobile_portal.webauth.utils import require_auth
from mobile_portal.osm.utils import fit_to_map
from mobile_portal.wurfl import device_parents
import geolocation

import pytz, simplejson, urllib

from models import FrontPageLink, ExternalImageSized, LocationShare
from forms import LocationShareForm, LocationShareAddForm
from utils import find_or_create_user_by_email
from ldap_queries import get_person_units

from handlers import BaseView

def index(request):
    internal_referer = request.META.get('HTTP_REFERER', '').startswith('http://oucs-alexd:8000/')
    internal_referer = request.META.get('HTTP_REFERER', '').startswith('http://m.ox.ac.uk/')

    if ("generic_web_browser" in device_parents[request.device.devid]
        and not request.preferences['core']['desktop_about_shown']
        and not request.GET.get('preview') == 'true'
        and not internal_referer):
        return HttpResponseRedirect(reverse('core_desktop_about'))

    # Take the default front age links from the database. If the user is logged
    # in we'll use the ones attached to their profile. If we've added new links
    # since last they visited, or if this is their first visit, we copy the
    # create references attached to their profile, which they can then edit.
    fpls = dict((fpl.slug, fpl) for fpl in FrontPageLink.objects.all())

    fpls_prefs = sorted(request.preferences['front_page_links'].items(), key=lambda (slug,(order, display)): order)

    front_page_links = [fpls[slug] for (slug,(order, display)) in fpls_prefs if display and slug in fpls]

    context = {
        'front_page_links': front_page_links,
    }
    return mobile_render(request, context, 'core/index')

def crisis(request):
    if request.user.is_authenticated():
        units = get_person_units(request.user.get_profile().webauth_username)
    else:
        units = [] 
    context = {
        'units': units,
    }
    return mobile_render(request, context, 'core/crisis')

class UpdateLocationView(BaseView):
    def initial_context(self, request):
        try:
            zoom = int(request.GET['zoom'])
        except (IndexError, KeyError):
            zoom = 16
        else:
            zoom = min(max(10, zoom), 18)
        return_url = (request.POST if request.method == 'POST' else request.GET).get('return_url')
        return {
            'zoom': zoom,
            'return_url': return_url,
        }

    def handle_GET(self, request, context):
        if 'location' in request.GET:
            return self.confirm_stage(request, context)
        else:
            return self.add_container_if_necessary(request, context, 'core/update_location')
            
    def handle_POST(self, request, context):
        try:
            title, accuracy, latitude, longitude = (
                request.POST['title'],
                float(request.POST['accuracy']),
                float(request.POST['latitude']),
                float(request.POST['longitude']),
            )
        except (KeyError, ValueError):
            return self.bad_request(request)
                
        location = latitude, longitude
        placemark = (title, location, accuracy)
        geolocation.set_location(request, location, accuracy, 'geocoded', placemark)
        
        if 'no_redirect' in request.POST:
            return HttpResponse('')
            
        if context['return_url']:
            response = HttpResponseRedirect(context['return_url'])
        else:
            response = HttpResponseRedirect(reverse('core_index'))
            
        response.status_code = 303
        return response

    def confirm_stage(self, request, context):
        location = request.GET['location']
        
        options = geolocation.geocode(location)

        points = [(o[1][0], o[1][1], 'red') for o in options]        
        
        if points:
            map_hash, (new_points, zoom) = fit_to_map(
                None,
                points = points,
                min_points = len(points),
                zoom = None,
                width = request.device.max_image_width,
                height = min(request.device.max_image_height, 200),
            )
        else:
            map_hash, zoom = None, None
        
        context.update({
            'zoom': zoom,
            'map_hash': map_hash,
            'options': options,
        })
        
        if request.GET.get('format') == 'json':
            return HttpResponse(
                simplejson.dumps(context),
                mimetype='application/json',
            )
        else:
            return self.add_container_if_necessary(request, context, 'core/update_location_confirm')
            
    def add_container_if_necessary(self, request, context, template_name):
        if request.GET.get('ajax') != 'true':
            template = loader.get_template(template_name+'.xhtml')
            context = RequestContext(request, context)
            
            context = {
                'content': template.render(context),
            }
            
            template_name = 'core/update_location_container'
        
        return mobile_render(request, context, template_name)
                    

def ajax_update_location(request):
    """
    This resource will only accept POST requests with the following arguments:

    'latitude' and 'longitude' [optional]
        Expressed in decimal degrees using the WGS84 projection.
    'accuracy' [optional]
        Expressed as a float in metres.
    'method' [required]
        One of 'html5', 'gears', 'manual', 'geocoded', 'other', 'denied', 'error'.

    If method is one of 'html5', 'gears', 'manual', 'other' then a position
    must be provided. If method is one of 'denied', 'error' then neither
    position nor accuracy may be provided.

    The methods have the following semantics:

    'html5'
        The position was determined using the HTML5 geolocation API, to be
        found in draft form at http://dev.w3.org/geo/api/spec-source.html.
    'gears'
        The position was determined using the Google Gears geolocation API,
        found at http://code.google.com/apis/gears/api_geolocation.html.
    'blackberry'
        The position was determined using the BlackBerry geolocation API,
        http://docs.blackberry.com/en/developers/deliverables/8861/blackberry_location_568404_11.jsp.
    'manual'
        The user provided the location directly.
    'geocoded'
        The user provided a string that was then geocoded to acquire a location.
    'other'
        Some other location method was used.
    'denied'
        A request was made to the user to be provided with the user's location
        but it was denied.
    'error'
        An unspecified error occured, as provided for in the HTML5 spec.

    If a location was provided, a successful request will return a reverse
    geocoded address if one is available, otherwise a space-delimited
    latitude-longitude pair. Without a location the empty string will be
    returned. In either case there will be an HTTP status code of 200.

    A request that does not meet this specification will result in an HTTP
    status code of 400, accompanied by a plain text body detailing the errors.
    """

    if request.method != 'POST':
        return HttpResponse(
            ajax_update_location.__doc__.replace('\n    ', '\n')[1:],
            status = 405,
            mimetype = 'text/plain',
        )

    errors = []

    # Decipher the location if given. Will through 400s in the following scenarios:
    #  * One or other of latitude and longitude isn't provided.
    #  * One or other of latitude and longitude isn't in the allowed range
    #  * One or other of latitude and longitude cannot be interpretted as a float.
    # If neither is provided then 
    location = request.POST.get('latitude'), request.POST.get('longitude')
    if any(location):
        try:
            location = tuple(map(float, location))
            lat, lon = location
            if not (-90 <= lat and lat <= 90 and -180 <= lon and lon < 180):
                raise ValueError
        except ValueError:
            errors.append(
                'Please provide latitude and longitude arguments as decimal degrees.',
            )
    else:
        location = None

    accuracy = request.POST.get('accuracy')
    if accuracy:
        try:
            accuracy = float(accuracy)
            if accuracy < 0:
                raise ValueError
            if not location:
                raise AssertionError
        except ValueError:
            errors.append(
                'If you provide accuracy, it must be a positive float expressed in metres.'
            )
        except AssertionError:
            errors.append(
                'You cannot specify accuracy without also providing a location.'
            )

    try:
        method = request.POST['method']
    except KeyError:
        errors.append(
            'You must provide a method.'
        )
    else:
        if method in ('html5', 'gears', 'manual', 'geocoded', 'blackberry', 'other'):
            if not location:
                errors.append(
                    'A position is required for the method you provided.'
                )
        elif method in ('denied', 'error'):
            if location:
                errors.append(
                    'You must not provide a position for the method you provided.'
                )
        else:
            errors.append(
                'The method you provided was not in the permitted set.'
            )

    if errors:
        return HttpResponse(
            """\
There were errors in the data you POST:

 * %s

For more information on acceptable requests perform a GET on this resource.
""" % "\n * ".join(errors),
            status=400,
            mimetype='text/plain'
        )

    if location:
        try:
            placemark = geolocation.reverse_geocode(*location)[0]
        except IndexError:
            placemark = None
    else:
        placemark = None

    geolocation.set_location(
        request,
        location,
        accuracy,
        method,
        placemark,
    )

    if location:
        if placemark:
            response_data = placemark[0]
        else:
            response_data = "%.4f %.4f" % location
    else:
        response_data = ''

    return HttpResponse(response_data, mimetype='text/plain')

@require_auth
def customise(request):
    post = request.POST or None
    links = request.user.get_profile().front_page_links.order_by('order')

    forms = [FrontPageLinkForm(post, instance=l, prefix="%d"%i) for i,l in enumerate(links)]

    if all(f.is_valid() for f in forms):
        forms.sort(key=lambda x:x.cleaned_data['order'])
        for i, f in enumerate(forms):
            f.cleaned_data['order'] = i+1
            f.save()
        return HttpResponseRedirect(reverse("core_index"))

    context = {
        'forms': forms,
    }
    return mobile_render(request, context, 'core/customise')

def external_image(request, slug):
    eis = get_object_or_404(ExternalImageSized, slug=slug)
    response = HttpResponse(open(eis.get_filename(), 'r').read(), mimetype='image/jpeg')
    last_updated = pytz.utc.localize(eis.external_image.last_updated)

    response['ETag'] = slug
    return response

@require_auth
def location_sharing(request):
    post = request.POST or None

    location_shares = LocationShare.objects.filter(from_user=request.user).order_by('from_user')
    location_share_forms = []
    for i, location_share in enumerate(location_shares):
        lsf = LocationShareForm(post, instance=location_share, prefix="%d" % i)
        location_share_forms.append( lsf )
    location_share_add_form = LocationShareAddForm(post)


    if post and 'location_share_add' in post:
        if location_share_add_form.is_valid():
            try:
                user = find_or_create_user_by_email(location_share_add_form.cleaned_data['email'], create_external_user=False)
            except ValueError:
                request.user.message_set.create(message="No user with that e-mail address exists.")
            else:
                if user in [ls.to_user for ls in location_shares]:
                    request.user.message_set.create(message="You are already sharing your location with that person.")
                else:
                    location_share = LocationShare(
                        from_user = request.user,
                        to_user = user,
                        accuracy = location_share_add_form.cleaned_data['accuracy'],
                    )
                    if location_share_add_form.cleaned_data['limit']:
                        location_share.until = datetime.now() + timedelta(hours=location_share_add_form.cleaned_data['limit'])
                    location_share.save()
                    response = HttpResponseRedirect('.')
                    response.status_code = 303
                    return response
        else:
            request.user.message_set.create(message="Please enter a valid e-mail address.")


    context = {
        'location_share_forms': location_share_forms,
        'location_share_add_form': location_share_add_form,
    }

    return mobile_render(request, context, 'core/location_sharing')

def run_command(request):
    if not request.user.is_superuser:
        raise Http404
    commands = {
        'update_podcasts': ('Update podcasts', []),
        'update_osm': ('Update OpenStreetMap data', []),
        'update_oxpoints': ('Update OxPoints data', []),
        'update_busstops': ('Update bus stop data', []),
        'update_rss': ('Update RSS feeds', []),
        'update_weather': ('Update weather feed', []),
        'generate_markers': ('Generate map markers', []),
        'pull_markers': ('Pull markers from external location', ['location']),
    }

    if request.method == 'POST':
        command = request.POST['command']

        if command in commands:
            arg_names = commands[request.POST['command']][1]
            args = {}
            for arg in arg_names:
                args[arg] = request.POST[arg]

            call_command(command, **args)

    context = {
        'commands': commands
    }

    return mobile_render(request, context, 'core/run_command')

def static_detail(request, title, template):
    t = loader.get_template('static/%s.xhtml' % template)

    context = {
        'title': title,
        'content': t.render(Context()),
    }
    return mobile_render(request, context, 'core/static_detail')

def desktop_about(request):
    return render_to_response('core/desktop_about.xhtml', {}, context_instance=RequestContext(request))    

def robots_txt(request):
    return HttpResponse("""
User-agent: *
Disallow: /update_location/
Disallow: /ajax_update_location/
""", mimetype="text/plain")