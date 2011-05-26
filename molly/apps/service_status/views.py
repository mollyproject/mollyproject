import logging
from django.utils.translation import ugettext as _

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

logger = logging.getLogger("molly.apps.service_status.views")


class IndexView(BaseView):
    """
    View to display service status information
    """

    # TODO Remove specific references to OUCS and OLIS
    def get_metadata(self, request):
        return {
            'title': _('Service Status'),
            'additional': _('Check whether OUCS and OLIS services are available'),
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb('service_status', None,
                          _('Service Status'),
                          lazy_reverse('index'))

    def handle_GET(self, request, context):
        services = []
        for provider in self.conf.providers:
            try:
                status = provider.get_status()
            except Exception, e:
                logger.warn("Failed to load service status", exc_info=True)
            else:
                services.append((
                    provider.slug, provider.name,
                    status['lastBuildDate'], status['services'],
                    provider.get_announcements(),
                ))

        
        context['services'] = services

        return self.render(request, context, 'service_status/index')
