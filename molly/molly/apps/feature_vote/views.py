from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breacrumb(
            cls.conf.local_name,
            None,
            'Feature suggestions',
            lazy_reverse('feature_voting:index'),
        )

    def handle_GET(cls, request, context):
        return cls.render(request, context, 'feature_voting/index')

