from django.http import Http404
from django.template import TemplateDoesNotExist

from molly.conf.urls import url
from molly.utils.views import BaseView
from molly.utils.breadcrumbs import Breadcrumb, BreadcrumbFactory, lazy_reverse

#@url(r'^(?P<view>[a-zA-Z0-9\-]+)/$', 'view')
@url(r'^$', 'index')
class StaticFileView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb('test',
                None,
                self.conf.title,
                lazy_reverse('index'))

    def handle_GET(self, request, context):
        try:
            return self.render(request, context, 'staticfiles/%s' % self.conf.local_name)
        except TemplateDoesNotExist:
            raise Http404
