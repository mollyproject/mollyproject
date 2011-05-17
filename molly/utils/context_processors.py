from urlparse import urlparse, urlunparse, parse_qs
from urllib import urlencode

from django.conf import settings

def site_name(request):
    return {
        'site_name': settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Molly Project'
    }
    
def full_path(request):
    scheme, netloc, path, params, query, fragment = \
        urlparse(request.get_full_path())
    args = []
    for k, vs in parse_qs(query).items():
        if k == 'format':
            continue
        else:
            for v in vs:
                args.append((k, v))
    query = urlencode(args)
    uri = urlunparse((scheme, netloc, path, params, query, fragment))
    return {
        'full_path': uri,
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
