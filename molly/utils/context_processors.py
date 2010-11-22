from django.conf import settings

def full_path(request):
    return {
        'full_path': request.get_full_path(),
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
        ssl_media_url = settings.MEDIA_URL.replace('http://', 'https://')
    else:
        ssl_media_url = settings.MEDIA_URL
  
    return {'MEDIA_URL': ssl_media_url}
