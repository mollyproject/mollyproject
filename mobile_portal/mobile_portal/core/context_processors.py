from datetime import datetime, timedelta
from mobile_portal.wurfl import device_parents

from mobile_portal.weather.models import Weather

DEVICE_SPECIFIC_MEDIA = {
#    'apple_iphone_ver1': {
#        'js': frozenset(['js/devices/apple_iphone.js']),
#        'css': frozenset(['css/devices/apple_iphone.css']),
#    },
    'blackberry_generic_ver4_sub10': {
        'js': frozenset(),
        'css': frozenset(['css/devices/rim_blackberry.css']),
    },
#    'generic': { # Firefox, actually
#        'js': frozenset(['js/devices/apple_iphone.js']),
#        'css': frozenset(['css/devices/apple_iphone.css']),
#    }
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

    dumb, smart, touch, multitouch, desktop = False, False, False, False, False
    if "apple_iphone_ver1" in device_parents[request.device.devid]:
        multitouch = True
    if request.device.pointing_method == 'touchscreen':
        touch = True
    if request.device.ajax_support_javascript:
        smart = True
    if "generic_web_browser" in device_parents[request.device.devid]:
        desktop = True
    dumb = not (smart or touch or multitouch or desktop)
    
    if "MSIE 4" in request.META.get('HTTP_USER_AGENT', ''):
        dumb, smart, touch, multitouch, desktop = True, False, False, False, False

    #dumb, smart, touch, multitouch, desktop = True, False, False, False, False
    
    return {
        'device_specific_media':media,
        'dumb': dumb,
        'smart': smart,
        'touch': touch,
        'multitouch': multitouch,
        'desktop': desktop,
    }    

def geolocation(request):
    """
    Provides location-based information to the template (i.e. lat/long, google
    placemark data, and whether we would like to request the device's location
    information.
    """
    
    # Use the epoch in the place of -inf; a time it has been a while since.
    epoch = datetime(1970,1,1, 0, 0, 0)
    
    # Only request a location if our current location is older than one minute
    # and the user isn't updating their location manually.
    # The one minute timeout applies to the more recent of a request and an
    # update.
    
    location = request.preferences['location']
    requested = location['requested'] or epoch
    updated = location['updated'] or epoch
    method = location['method'] or epoch
    
    if max(requested, updated) + timedelta(0, 60) < datetime.now() and method in ('html5', 'gears', None):
        require_location = True
        location['requested'] = datetime.now()
    else:
        require_location = False
    
    location = request.session.get('location')
    placemark = request.session.get('placemark')
    
    return {
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
        'common_name': request.session.get('common_name'),
        'preferences': request.preferences
    }
    