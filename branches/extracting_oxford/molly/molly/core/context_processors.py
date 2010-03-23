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
    
