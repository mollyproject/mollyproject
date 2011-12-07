from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from models import Weather

class IndexView(BaseView):
    def initial_context(self, request):
        try:
            observation = Weather.objects.get(location_id=self.conf.location_id, ptype='o')
        except Weather.DoesNotExist:
            observation = None
        copyrights = [provider.copyright for provider in self.conf.providers]
        return {
            'observation': observation,
            'copyrights': copyrights,
            'forecasts': Weather.objects.filter(
                location_id=self.conf.location_id, ptype='f',
                observed_date__gte=datetime.now().date()).order_by('observed_date'),
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            'weather',
            None,
            _('Weather'),
            lazy_reverse('index'),
        )

    def handle_GET(self, request, context):
        return self.render(request, context, 'weather/index',
                           expires=timedelta(minutes=10))
