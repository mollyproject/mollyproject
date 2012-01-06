from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

from molly.conf.urls import url
from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from molly.apps.weather.models import Weather

@url(r'^$', 'index')
class IndexView(BaseView):
    """
    Displays current weather observations and forecasts for the next 3 days
    """
    
    def _is_fresh(self, observation, freshness):
        return datetime.now() - freshness < observation.observed_date
    
    def initial_context(self, request):
        try:
            observation = self.conf.provider.fetch_observation()
        except Weather.DoesNotExist:
            observation = None

        return {
            'observation': observation,
            'attribution': self.conf.provider.ATTRIBUTION,
            'fresh': self._is_fresh(observation, self.conf.provider.FRESHNESS),
            'forecasts': self.conf.provider.fetch_forecasts(),
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
