from mobile_portal.core.renderers import mobile_render
from models import Weather


def index(request):
    context = {
        'weather': Weather.objects.get(bbc_id=25),
    }
    return mobile_render(request, context, 'weather/index')