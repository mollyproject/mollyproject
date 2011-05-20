from datetime import timedelta

from django.http import Http404

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Maps',
            lazy_reverse('maps:osm-about'),
        )

    def handle_GET(self, request, context):
        raise Http404

class TouchMapLiteView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Maps',
            lazy_reverse('maps:touchmaplite'),
        )

    def handle_GET(self, request, context):
        context.update({
            'zoom_controls': True,
        })
        return self.render(request, context, 'maps/touchmaplite/map',
                           expires=timedelta(days=365))