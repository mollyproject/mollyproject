from datetime import timedelta
from xml.sax.saxutils import escape

from django.shortcuts import get_object_or_404
from django.http import Http404

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.external_media import resize_external_image

from molly.apps.webcams.models import Webcam, WEBCAM_WIDTHS

import datetime

class IndexView(BaseView):
    def get_metadata(self, request):
        return {
            'title': 'Webcams',
            'additional': 'View webcams from around the city and University',
        }
        
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(self.conf.local_name, None, 'Webcams', lazy_reverse('index'))
        
    def handle_GET(self, request, context):
        webcams = Webcam.objects.all()
        context['webcams'] = webcams
        return self.render(request, context, 'webcams/index',
                           expires=timedelta(days=7))
    
class WebcamDetailView(BaseView):
    def get_metadata(self, request, slug):
        webcam = get_object_or_404(Webcam, slug=slug)
        return {
            'title': webcam.title,
            'additional': '<strong>Webcam</strong>, %s' % escape(webcam.description)
        }
        
    def initial_context(self, request, slug):
        return {
            'webcam': get_object_or_404(Webcam, slug=slug)
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, slug):
        return Breadcrumb(self.conf.local_name, lazy_parent('index'),
                          'Webcam', lazy_reverse('webcams', args=[slug]))
        
    def handle_GET(self, request, context, slug):
        try:
            eis = resize_external_image(
                context['webcam'].url,
                request.map_width, timeout=5)
        except:
            eis = None
        
        context['eis'] = eis
        return self.render(request, context, 'webcams/webcam_detail')
