from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

class IndexView(BaseView):
    """
    View to display the OUCS service status information.
    """

    def get_metadata(cls, request):
        return {
            'title': 'Service Status',
            'additional': 'Check whether OUCS and OLIS services are available',
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb('service_status', None,
                          'Service Status',
                          lazy_reverse('service_status:index'))

    def handle_GET(cls, request, context):
        services = []
        for provider in cls.conf.providers:
            services.append((
                provider.slug, provider.name,
                provider.get_status(),
                provider.get_announcements(),
            ))

        context['services'] = services

        return cls.render(request, context, 'service_status/index')

