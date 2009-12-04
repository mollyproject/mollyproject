from datetime import datetime, timedelta
from mobile_portal.wurfl import device_parents

from mobile_portal.weather.models import Weather
from mobile_portal.core.models import UserMessage

DEVICE_SPECIFIC_MEDIA = {
#    'apple_iphone_ver1': {
#        'js': frozenset(['js/devices/apple_iphone.js']),
#        'css': frozenset(['css/devices/apple_iphone.css']),
#    },
#    'blackberry_generic_ver4_sub10': {
#        'js': frozenset(),
#        'css': frozenset(['css/devices/rim_blackberry.css']),
#    },
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

    device, browser = request.device, request.browser
    
    # Skyfire
    if browser.devid == 'generic_skyfire':
        style_group = "dumb"
        
    # Apple products
    elif device.brand_name == 'Apple' :
        style_group = "smart"
        
    # Symbian S60 v3 and above (iresspective of browser)
    elif device.device_os == 'Symbian' and tuple(map(int, device.device_os_version.split('.'))) >= 9.2 : 
        style_group = "smart"
    # Nokia Maemo 
    elif device.brand_name == 'Nokia' and device.device_os == 'Linux Smartphone OS' :
        style_group = "smart"
        
    # Blackberries 
    elif device.brand_name == 'RIM' :
        style_group = 'smart'
        
    # Android
    elif device.device_os == 'Android' :
        style_group = 'smart'
        
    # Palm Web OS
    elif device.device_os == 'Web OS' :
        style_group = 'smart'
        
    # Opera Mini/Mobile Browsers
    elif browser.brand_name == 'Opera':
        style_group = 'smart'
        
    # Desktop browsers
    elif 'generic_web_browser' in device_parents[browser.devid]:
        style_group = 'smart'
        
    # All Others
    else:
        style_group = "dumb"
    return {
        'style_group': style_group,
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
        'browser': request.browser,
        'device': request.device,
        'map_width': request.map_width,
        'map_height': request.map_height,
        'meta': dict((a,b) for (a,b) in request.META.items() if a.startswith('HTTP_')),
    }

from django.db import connection

def weather(request):
    """
    Adds weather information to the context in keys 'weather' and 'weather_icon'.
    """

    return {
        
        # This comes from LDAP and should be moved to its own context processor.
        'common_name': request.session.get('common_name'),
        'preferences': request.preferences,
        'session_key': request.session.session_key,
        'queries': connection.queries,
        'path': request.path,
        'unread_user_messages': UserMessage.objects.filter(session_key = request.session.session_key, read=False).count() > 0,
    }
    
