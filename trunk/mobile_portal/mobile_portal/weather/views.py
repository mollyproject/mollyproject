from datetime import datetime
from mobile_portal.core.renderers import mobile_render

from mobile_portal.core.handlers import BaseView
from mobile_portal.core.breadcrumbs import Breadcrumb, BreadcrumbFactory, lazy_reverse

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
