from django.http import Http404

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            cls.conf.local_name,
            None,
            'Maps',
            lazy_reverse('maps:osm-about'),
        )

    def handle_GET(cls, request, context):
        raise Http404