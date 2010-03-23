from datetime import datetime, timedelta
from molly.wurfl import device_parents

from molly.core.models import UserMessage

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
    use_javascript = True

    # Skyfire
    if browser.devid == 'generic_skyfire':
        style_group = "dumb"

    # Apple products
    elif device.brand_name == 'Apple' :
        style_group = "smart"

    # Symbian S60 v3 and above (iresspective of browser)
    elif device.device_os in ('Symbian', 'Symbian OS') and tuple(map(int, device.device_os_version.split('.'))) >= (9, 2) :
        style_group = "smart"

    # Nokia Maemo
    elif device.brand_name == 'Nokia' and device.device_os == 'Linux Smartphone OS' :
        style_group = "smart"

    # Blackberries
    elif device.brand_name == 'RIM' :
        style_group = 'smart'
        use_javascript = False

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
        use_javascript = False

    return {
        'style_group': style_group,
        'use_javascript': use_javascript,
    }



def weather(request):
    """
    Adds weather information to the context in keys 'weather' and 'weather_icon'.
    """

    return {
        
        # This comes from LDAP and should be moved to its own context processor.
        'common_name': request.session.get('common_name'),
        'preferences': request.preferences,
        'session_key': request.session.session_key,
        'path': request.path,
        'full_path': request.get_full_path(),
        'unread_user_messages': UserMessage.objects.filter(session_key = request.session.session_key, read=False).count() > 0,
    }
    
