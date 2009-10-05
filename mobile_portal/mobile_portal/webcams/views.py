# Create your views here.

from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404

from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.models import Feed
from mobile_portal.core.utils import resize_external_image
from models import Webcam, WEBCAM_WIDTHS


def index(request):
    webcams = Webcam.objects.all()
    context = {
        'webcams': webcams,
    }
    return mobile_render(request, context, 'webcams/index')
    
def webcam_detail(request, slug):
    webcam = get_object_or_404(Webcam, slug=slug)
    
    try:
        eis = resize_external_image(webcam.url, request.device.max_image_width, timeout=5)
    except (IOError, urllib2.URLError):
        eis = None
    except:
        raise
    
    context = {
        'webcam': webcam,
        'eis': eis,
    }
    return mobile_render(request, context, 'webcams/webcam_detail')
