# Create your views here.

from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404

from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.models import Feed
from models import Webcam, WEBCAM_WIDTHS


def index(request):
    webcams = Webcam.objects.all()
    context = {
        'webcams': webcams,
    }
    return mobile_render(request, context, 'webcams/index')
    
def webcam_detail(request, slug):
    webcam = get_object_or_404(Webcam, slug=slug)
    
    context = {
        'webcam': webcam,
    }
    return mobile_render(request, context, 'webcams/webcam_detail')
