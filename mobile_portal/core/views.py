# Create your views here.
from datetime import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from mobile_portal.core.renderers import mobile_render
import geolocation

import sys, traceback

def index(request):
    print "\n".join("%20s : %s" % s for s in request.META.items() if s[0].startswith('HTTP_'))
    context = {
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
        
        elif len(position) > 1:
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
        
        geolocation.set_location(request, placemark, *location, method='geoapi')

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
        