from urlparse import urlparse, urlunparse, parse_qs
from urllib import urlencode

from django.conf import settings
from django.utils.translation import ugettext as _

from molly.utils.i18n import override
from molly.utils.views import tidy_query_string

def site_name(request):
    return {
        'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Molly Project'
    }

def languages(request):
    languages = []
    for language_code, language_name in settings.LANGUAGES:
        with override(language_code):
            languages.append((language_code, _(language_name)))
    return {
        'LANGUAGES': languages,
    }

def full_path(request):
    return {
        'full_path': tidy_query_string(request.get_full_path()),
    }

def google_analytics(request):
    return {
        'google_analytics': settings.API_KEYS.get('google_analytics'),
    }

def ssl_media(request):
    """
    If the request is secure, then the media url should be HTTPS
    
    Source: http://djangosnippets.org/snippets/1754/
    """

    if request.is_secure():
        ssl_media_url = settings.STATIC_URL.replace('http://', 'https://')
    else:
        ssl_media_url = settings.STATIC_URL
  
    return {'STATIC_URL': ssl_media_url}
