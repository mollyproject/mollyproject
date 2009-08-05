# Create your views here.
from datetime import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from mobile_portal.core.renderers import mobile_render
from mobile_portal.webauth.utils import require_auth
import geolocation

import sys, traceback

from models import FrontPageLink
from forms import FrontPageLinkForm

def index(request):
    print "\n".join("%20s : %s" % s for s in request.META.items() if s[0].startswith('HTTP_'))
    
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
    context = {
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
            
            return HttpResponseRedirect(reverse('core_index'))
        
        elif len(placemarks) > 1:
            options = placemarks
        else:
            error='We could not determine where that place is. Please try again.'
            
    print options
    context = {
        'error': error,
        'options': options,
        'location': request.POST.get('location', '')
    }
    return mobile_render(request, context, 'core/update_location')

def ajax_update_location(request):
    try:
        location = (float(request.POST['latitude']), float(request.POST['longitude']))
        try:
            placemark = geolocation.reverse_geocode(*location)[0]
        except IndexError:
            placemark = None
        
        geolocation.set_location(request, placemark, location[0], location[1], method='geoapi')

        request.session['location'] = location
        request.session['location_updated'] = datetime.now()
        request.session['placemark'] = placemark

    except (ValueError, KeyError), e:
        pass
        
    if request.session.get('placemark'):
        address = request.session['placemark']['address']
    else:
        address = "%s %s" % request.session['location']
    
    return HttpResponse(address)

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
