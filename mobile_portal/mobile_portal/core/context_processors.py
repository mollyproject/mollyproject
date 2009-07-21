from datetime import datetime, timedelta
from mobile_portal.wurfl import device_parents

DEVICE_SPECIFIC_MEDIA = {
    'apple_iphone_ver1': {
        'js': frozenset(['js/devices/apple_iphone.js']),
        'css': frozenset(['css/devices/apple_iphone.css']),
    },
    'blackberry_generic_ver4_sub10': {
        'js': frozenset(),
        'css': frozenset(['css/devices/rim_blackberry.css']),
    },
    'stupid_novarra_proxy_sub73': {
        'js': frozenset(['js/devices/apple_iphone.js']),
        'css': frozenset(['css/devices/apple_iphone.css']),
    }
}

DEVICE_SPECIFIC_MEDIA_SET = frozenset(DEVICE_SPECIFIC_MEDIA)

def device_specific_media(request):
    media = {'js':set(), 'css':set()}
    
    for devid in DEVICE_SPECIFIC_MEDIA_SET & device_parents[request.device.devid]:
        for key in media:
            media[key] |= DEVICE_SPECIFIC_MEDIA[devid][key]

    return {
        'device_specific_media':media,
    }    

def geolocation(request):
    epoch = datetime(1970,1,1, 0, 0, 0)
    s = request.session
    if max(s.get('location_requested', epoch), s.get('location_updated', epoch)) + timedelta(0, 300) < datetime.now() and s.get('location_method') in ('geoapi', None):
        require_location = True
        request.session['location_requested'] = datetime.now()
    else:
        require_location = False
    
    location = request.session.get('location')
    placemark = request.session.get('placemark')
    #raise Exception(location)
    
    
    return {
        'session': request.session.items(),
        'location': location,
        'location_updated': request.session.get('location_updated'),
        'placemark': placemark,
        'require_location': require_location,
        'device': request.device,
        'meta': dict((a,b) for (a,b) in request.META.items() if a.startswith('HTTP_')),
    }
