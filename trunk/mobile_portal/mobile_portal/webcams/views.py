# Create your views here.

from xml.sax.saxutils import escape

from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404

from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.models import Feed
from mobile_portal.core.handlers import BaseView
from mobile_portal.core.utils import resize_external_image
from models import Webcam, WEBCAM_WIDTHS


class IndexView(BaseView):
    def get_metadata(self, request):
        return {
            'title': 'Webcams',
            'additional': 'View webcams from around the city and University',
        }
        
    def handle_GET(self, request, context):
        webcams = Webcam.objects.all()
        context = {
            'webcams': webcams,
        }
        return mobile_render(request, context, 'webcams/index')
    
class WebcamDetailView(BaseView):
    def get_metadata(self, request, slug):
        webcam = get_object_or_404(Webcam, slug=slug)
        return {
            'title': webcam.title,
            'additional': '<strong>Webcam</strong>, %s' % escape(webcam.description)
        }
        
    def handle_GET(self, request, context, slug):
        webcam = get_object_or_404(Webcam, slug=slug)
        
        try:
            eis = resize_external_image(webcam.url, request.device.max_image_width, timeout=5)
        except:
            eis = None
        
        context = {
            'webcam': webcam,
            'eis': eis,
        }
        return mobile_render(request, context, 'webcams/webcam_detail')
