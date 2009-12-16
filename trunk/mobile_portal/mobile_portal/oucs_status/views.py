import feedparser
from mobile_portal.core.handlers import BaseView
from mobile_portal.core.breadcrumbs import Breadcrumb, BreadcrumbFactory, lazy_reverse
from mobile_portal.core.renderers import mobile_render

class IndexView(BaseView):
    """
    View to display the OUCS service status information.
    """

    STATUS_URL = 'http://status.ox.ac.uk/verboserss.xml'

    def get_metadata(cls, request):
        return {
            'title': 'OUCS Service Status',
            'additional': 'Check whether OUCS services are available',
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb('oucs_status', None,
                          'OUCS Service Status',
                          lazy_reverse('oucs_status_index'))

    def handle_GET(cls, request, context):
        services_feed = feedparser.parse(cls.STATUS_URL)
        services = context['services'] = []
        for service_feed in services_feed.entries:
            service = {
                'name': service_feed.title,
                'detail': service_feed.get('description', None),
                'status': cls.get_category(service_feed.category),
            }
            services.append(service)
        return mobile_render(request, context, 'oucs_status/index')

    def get_category(cls, name):
        """
        Normalises status names to a set we can have icons for.
        """
        name = (name or '').lower()
        if name in ('up', 'down', 'partial', 'unknown'):
            return name
        elif name == 'Web interface is not responding':
            return 'unknown'
        else:
            return 'unknown'
