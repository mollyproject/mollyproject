from datetime import datetime

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils.renderers import mobile_render

from models import Weather

class IndexView(BaseView):
    def initial_context(cls, request):
        try:
            observation = Weather.objects.get(location_id=cls.conf.location_id, ptype='o')
        except Weather.DoesNotExist:
            observation = None
        return {
            'observation': observation,
            'forecasts': Weather.objects.filter(location_id=cls.conf.location_id, ptype='f', observed_date__gte=datetime.now().date()).order_by('observed_date'),
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'weather',
            None,
            'Weather',
            lazy_reverse('weather:index'),
        )

    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'weather/index')
