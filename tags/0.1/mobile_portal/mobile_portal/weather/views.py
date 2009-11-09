from datetime import datetime
from mobile_portal.core.renderers import mobile_render
from models import Weather


def index(request):
    context = {
        'weather': Weather.objects.get(bbc_id=25, ptype='o'),
        'forecasts': Weather.objects.filter(bbc_id=25, ptype='f', observed_date__gte=datetime.now().date()).order_by('observed_date'),
    }
    return mobile_render(request, context, 'weather/index')