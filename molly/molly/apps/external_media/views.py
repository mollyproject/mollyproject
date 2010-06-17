import pytz

from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import NullBreadcrumb

from models import ExternalImageSized

class IndexView(BaseView):
    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context):
        raise Http404

class ExternalImageView(BaseView):

    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context, slug):
        eis = get_object_or_404(ExternalImageSized, slug=slug)
        response = HttpResponse(open(eis.get_filename(), 'r').read(), mimetype=eis.content_type)
        last_updated = pytz.utc.localize(eis.external_image.last_updated)

        response['ETag'] = slug
        return response

