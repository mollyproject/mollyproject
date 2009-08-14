from datetime import datetime, timedelta
from mobile_portal.wurfl import device_parents

from mobile_portal.weather.models import Weather

DEVICE_SPECIFIC_MEDIA = {
    'apple_iphone_ver1': {
        'js': frozenset(['js/devices/apple_iphone.js']),
        'css': frozenset(['css/devices/apple_iphone.css']),
    },
    'blackberry_generic_ver4_sub10': {
        'js': frozenset(),
        'css': frozenset(['css/devices/rim_blackberry.css']),
    },
    'stupid_novarra_proxy_sub73': { # Firefox, actually
        'js': frozenset(['js/devices/apple_iphone.js']),
        'css': frozenset(['css/devices/apple_iphone.css']),
    }
}

DEVICE_SPECIFIC_MEDIA_SET = frozenset(DEVICE_SPECIFIC_MEDIA)

def device_specific_media(request):
    """
    Uses DEVICE_SPECIFIC_MEDIA as a basis to pass extra context when the
    wurfl-detected device is a child of a given device id.
    """
    
    media = {'js':set(), 'css':set()}
    
    for devid in DEVICE_SPECIFIC_MEDIA_SET & device_parents[request.device.devid]:
        for key in media:
            media[key] |= DEVICE_SPECIFIC_MEDIA[devid][key]

    return {
        'device_specific_media':media,
    }    

def geolocation(request):
    """
    Provides location-based information to the template (i.e. lat/long, google
    placemark data, and whether we would like to request the device's location
    information.
    """
    
    # Use the epoch in the place of -inf; a time it has been a while since.
    epoch = datetime(1970,1,1, 0, 0, 0)
    s = request.session
    # Only request a location if our current location is older than one minute
    # and the user isn't updating their location manually.
    # The one minute timeout applies to the more recent of a request and an
    # update.
    if max(s.get('location_requested', epoch), s.get('location_updated', epoch)) + timedelta(0, 60) < datetime.now() and s.get('location_method') in ('geoapi', None):
        require_location = True
        request.session['location_requested'] = datetime.now()
    else:
        require_location = False
    
    location = request.session.get('location')
    placemark = request.session.get('placemark')
    
    return {
        'location': location,
        'location_updated': request.session.get('location_updated'),
        'placemark': placemark,
        'require_location': require_location,

        # Debug information follows.        
        'session': request.session.items(),
        'device': request.device,
        'meta': dict((a,b) for (a,b) in request.META.items() if a.startswith('HTTP_')),
    }

def weather(request):
    """
    Adds weather information to the context in keys 'weather' and 'weather_icon'.
    """
    
    try:
        weather = Weather.objects.get(bbc_id=25)
    except Weather.DoesNotExist:
        weather = None
    
    return {
        'weather': weather,
        
        # This comes from LDAP and should be moved to its own context processor.
        'common_name': request.session.get('common_name')
    }
    