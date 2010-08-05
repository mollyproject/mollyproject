from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from .models import Idea

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            cls.conf.local_name,
            None,
            'Feature suggestions',
            lazy_reverse('feature_voting:index'),
        )

    def initial_context(cls, request):
        return {
            'ideas': Idea.objects.all(),
        }

    def handle_GET(cls, request, context):
        return cls.render(request, context, 'feature_voting/index')

