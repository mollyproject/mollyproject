from datetime import datetime

from mobile_portal.utils.views import BaseView
from mobile_portal.utils.breadcrumbs import *
from mobile_portal.utils.renderers import mobile_render

from models import Weather

class IndexView(BaseView):
    def initial_context(cls, request):
        return {
            'weather': Weather.objects.get(bbc_id=25, ptype='o'),
            'forecasts': Weather.objects.filter(bbc_id=25, ptype='f', observed_date__gte=datetime.now().date()).order_by('observed_date'),
        }
    
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'weather',
            None,
            'Weather',
            lazy_reverse('weather_index'),
        )
        
    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'weather/index')
