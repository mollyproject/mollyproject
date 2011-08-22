from datetime import timedelta

from django.http import Http404
from django.utils.translation import ugettext as _

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            _('Maps'),
            lazy_reverse('maps:osm-about'),
        )

    def handle_GET(self, request, context):
        raise Http404
