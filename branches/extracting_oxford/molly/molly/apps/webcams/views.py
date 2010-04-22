# Create your views here.

from xml.sax.saxutils import escape

from django.shortcuts import get_object_or_404
from django.http import Http404

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from molly.apps.home.utils import resize_external_image
from models import Webcam, WEBCAM_WIDTHS

class IndexView(BaseView):
    def get_metadata(cls, request):
        return {
            'title': 'Webcams',
            'additional': 'View webcams from around the city and University',
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb('webcams', None, 'Webcams', lazy_reverse('webcams:index'))
        
    def handle_GET(cls, request, context):
        webcams = Webcam.objects.all()
        context['webcams'] = webcams
        return cls.render(request, context, 'webcams/index')
    
class WebcamDetailView(BaseView):
    def get_metadata(cls, request, slug):
        webcam = get_object_or_404(Webcam, slug=slug)
        return {
            'title': webcam.title,
            'additional': '<strong>Webcam</strong>, %s' % escape(webcam.description)
        }
        
    def initial_context(cls, request, slug):
        return {
            'webcam': get_object_or_404(Webcam, slug=slug)
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, slug):
        return Breadcrumb('webcams', lazy_parent(IndexView),
                          'Webcam', lazy_reverse('webcams:webcam', args=[slug]))
        
    def handle_GET(cls, request, context, slug):
        try:
            eis = resize_external_image(
                context['webcam'].url,
                request.map_width, timeout=5)
        except:
            eis = None
        
        context['eis'] = eis
        return cls.render(request, context, 'webcams/webcam_detail')
