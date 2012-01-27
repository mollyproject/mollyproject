from django.http import Http404
from django.template import TemplateDoesNotExist

from molly.conf.urls import url
from molly.utils.views import BaseView
from molly.utils.breadcrumbs import Breadcrumb, BreadcrumbFactory, lazy_reverse, lazy_parent


class PageView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(self, request, context, page='index'):
        parent = None
        if page != 'index':
            parent = lazy_parent('index')
        return Breadcrumb(self.conf.local_name,
                parent,
                self.conf.title,
                lazy_reverse(page))

    def get_metadata(self, request):
        return {
            'title': self.conf.title,
        }

    def handle_GET(self, request, context, page='index'):
        try:
            return self.render(request, context, 'staticfiles/%s/%s'
                    % (self.conf.local_name, page))
        except TemplateDoesNotExist:
            raise Http404
