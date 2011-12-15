from datetime import datetime, timedelta
from django.utils.translation import ugettext as _

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from models import Weather

class IndexView(BaseView):
    def initial_context(self, request):
        """
        Provides intiial context for main view. 
        Caveats: We can only handle one data provider AND observation at a time
        """
        try:
            # This will except of more than one observation is found.
            observation = Weather.objects.get(location_id=self.conf.location_id, ptype='o')
        except Weather.DoesNotExist:
            observation = None
        # This returns a list of attributions, but we can't tie it to an 
        # observation or forecast at present. 
        attributions = [provider.attribution for provider in self.conf.providers]
        freshness = [provider.freshness for providder in self.conf.providers][0]

        # Check if the we have recent data. 
        # NB This is not the same as checking if the provider has received data
        # recently.
        fresh = True
        if datetime.now() - observation.observed_date > freshness:
            fresh = False

        return {
            'observation': observation,
            'attributions': attributions,
            'fresh': fresh,
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
