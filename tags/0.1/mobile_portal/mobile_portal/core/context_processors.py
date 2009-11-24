from datetime import datetime, timedelta
from mobile_portal.wurfl import device_parents

from mobile_portal.weather.models import Weather
from mobile_portal.core.models import UserMessage

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


#Symbian
    #if request.device.device_os == 'Symbian OS' and float(request.device.device_os_version) >= 9.2 and request.device.mobile_browser == 'Safari':
	        #media['js'].add( 'js/some/file.js' )
	        #media['css'].add( 'css/classes/touch.css' )
	
	
	
#Windows Mobile	
    ## Pocket Internet Explorer

    # v5 or below
    #if request.device.device_os == 'Windows Mobile OS' and float(request.device.device_os_version) < 6.0 and request.device.mobile_browser in ('Internet Explorer', 'Microsoft Mobile Explorer'):
            #fail.

    # v6
    #if request.device.device_os == 'Windows Mobile OS' and float(request.device.device_os_version) == 6.0 and request.device.mobile_browser in ('Internet Explorer', 'Microsoft Mobile Explorer'):
            #fail.

    # v6.1
	#if request.device.device_os == 'Windows Mobile OS' and float(request.device.device_os_version) == 6.1 and request.device.mobile_browser in ('Internet Explorer','Microsoft Mobile Explorer'):
		    #fail.

    # v6.5
            #fail.


    
    

#Blackberry
# <= 5.0
# <= 4.5

#Palm - Web OS

#Apple iPhone
# v2
# v3

#Android
##1.5 Cupcake
## 1.6 Donut
## 2.0 Eclair

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
    