from django.conf import settings

def full_path(request):
    return {
        'full_path': request.get_full_path(),
    }

def google_analytics(request):
    return {
        'google_analytics': settings.API_KEYS.get('google_analytics'),
    }