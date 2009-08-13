# Create your views here.
from datetime import datetime, timedelta
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.conf import settings
from mobile_portal.core.renderers import mobile_render
from mobile_portal.webauth.utils import require_auth
import geolocation

import sys, traceback, pytz

from models import FrontPageLink, ExternalImageSized, LocationShare
from forms import FrontPageLinkForm, LocationShareForm, LocationShareAddForm
from utils import find_or_create_user_by_email
from ldap_queries import get_person_units

def index(request):
    #print "\n".join("%20s : %s" % s for s in request.META.items() if s[0].startswith('HTTP_'))
    
    # Take the default front age links from the database. If the user is logged
    # in we'll use the ones attached to their profile. If we've added new links
    # since last they visited, or if this is their first visit, we copy the
    # create references attached to their profile, which they can then edit.
    front_page_links = FrontPageLink.objects.order_by('order')    
    if request.user.is_authenticated():
        user_front_page_links = request.user.get_profile().front_page_links.order_by('order')
        if front_page_links.count != user_front_page_links.count:
            for link in front_page_links:
                if not link in [l.front_page_link for l in user_front_page_links]:
                    request.user.get_profile().front_page_links.create(
                        front_page_link = link,
                        order = link.order,
                        displayed = link.displayed
                    )
            front_page_links = request.user.get_profile().front_page_links.filter(displayed=True).order_by('order')
        else:
            front_page_links = user_front_page_links
    front_page_links = [l for l in front_page_links if l.displayed]

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

def update_location(request):
    error = ''
    options = []

    if request.method == 'POST':
        placemarks = geolocation.geocode(request.POST.get('location'))
        try:
            index = int(request.POST.get('index'))
        except (TypeError, ValueError):
            index = None
        
        if len(placemarks) == 1 or not index is None:
            try:
                placemark = placemarks[index]
            except:
                placemark = placemarks[0]

            geolocation.set_location(request, placemark, method='manual')
            
            try:
                response = HttpResponseRedirect(request.POST['return_url'])
            except KeyError:
                response = HttpResponseRedirect(reverse('core_index'))
            response.status_code = 303
            return response
        
        elif len(placemarks) > 1:
            options = placemarks
        else:
            error='We could not determine where that place is. Please try again.'
            
    context = {
        'error': error,
        'options': options,
        'location': request.POST.get('location', ''),
        'return_url': request.GET.get('return_url') or request.POST.get('return_url')
    }
    return mobile_render(request, context, 'core/update_location')

def ajax_update_location(request):
    try:
        location = (float(request.POST['latitude']), float(request.POST['longitude']))
        
        lat, lon = location
        if not (-90 <= lat and lat < 90 and -180 <= lon and lon < 180):
            raise ValueError

        try:
            placemark = geolocation.reverse_geocode(*location)[0]
        except IndexError:
            placemark = None
        
        geolocation.set_location(request, placemark, location[0], location[1], method='geoapi')

        request.session['location'] = location
        request.session['location_updated'] = datetime.now()
        request.session['placemark'] = placemark

            
    except (ValueError, KeyError), e:
        return HttpResponse('Please provide latitude and longitude arguments in a POST as decimal degrees.', status=400, mimetype='text/plain')
        
    if request.session.get('placemark'):
        address = request.session['placemark']['address']
    else:
        address = "%s %s" % request.session['location']
    
    return HttpResponse(address, mimetype='text/plain')

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
        return HttpResponseRedirect('.') 

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
    