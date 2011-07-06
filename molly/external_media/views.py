from email.utils import formatdate
from datetime import datetime, timedelta
from time import mktime

from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import NullBreadcrumb

from models import ExternalImageSized


class IndexView(BaseView):
    breadcrumb = NullBreadcrumb

    def handle_GET(self, request, context):
        raise Http404


class ExternalImageView(BaseView):

    breadcrumb = NullBreadcrumb

    def handle_GET(self, request, context, slug):
        eis = get_object_or_404(ExternalImageSized, slug=slug)
        try:
            response = HttpResponse(open(eis.get_filename(), 'rb').read(),
                                    mimetype=eis.content_type.encode('ascii'))
        except IOError:
            eis.delete()
            raise Http404()

        response['ETag'] = slug
        response['Expires'] = formatdate(mktime((datetime.now() + timedelta(days=7)).timetuple()))
        response['Last-Modified'] = formatdate(mktime(eis.external_image.last_updated.timetuple()))
        return response
