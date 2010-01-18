import feedparser, random

from mobile_portal.utils.views import BaseView
from mobile_portal.utils.breadcrumbs import *
from mobile_portal.utils.renderers import mobile_render


class IndexView(BaseView):
    """
    View to display the OUCS service status information.
    """

    STATUS_URL = 'http://status.ox.ac.uk/verboserss.php'
    ANNOUNCE_URL = 'http://status.ox.ac.uk/oxitems/generatersstwo2.php?channel_name=oucs/status-announce'

    OLIS_URL = 'http://www.lib.ox.ac.uk/olis/status/olis-opac.rss'

    def get_metadata(cls, request):
        return {
            'title': 'Service Status',
            'additional': 'Check whether OUCS and OLIS services are available',
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb('service_status', None,
                          'Service Status',
                          lazy_reverse('service_status_index'))

    def handle_GET(cls, request, context):
        services_feed = feedparser.parse(cls.STATUS_URL)
        
        oucs_services = []
        for service_feed in services_feed.entries:
            service = {
                'name': service_feed.title,
                'detail': service_feed.get('description'),
                'status': cls.get_category(service_feed.category),
            }
            oucs_services.append(service)
        
        services_feed = feedparser.parse(cls.OLIS_URL)
        olis_services = []
        for service in services_feed.entries:
            service = {
                'name': service.title,
                'detail': service.get('ss_statusMessage'),
                'status': cls.map_availability(service),
            }
            olis_services.append(service)
            
        context['all_services'] = (
            ('OUCS', oucs_services),
            ('OLIS', olis_services),
        )
        
        context['announce'] = feedparser.parse(cls.ANNOUNCE_URL)
        #context['all_up'] = all(s['status'] == 'up' for s in services)
        return mobile_render(request, context, 'service_status/index')

    def get_category(cls, name):
        """
        Normalises status names to a set we can have icons for.
        """
        #return random.choice(('up', 'down', 'partial', 'unknown'))
        name = (name or '').lower()
        if name in ('up', 'down', 'partial', 'unknown'):
            return name
        elif name == 'Web interface is not responding':
            return 'unknown'
        else:
            return 'unknown'

    def map_availability(cls, service):
        #return random.choice(('up', 'down', 'partial', 'unknown'))
        try:
            availability = int(service.ss_availability)
        except:
            return 'up' if service.ss_responding == 'true' else down
        else:
            return {0:'down', 100:'up'}.get(service.ss_availability, 'partial')