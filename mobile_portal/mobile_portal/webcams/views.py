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
    a = request.device.max_image_width
    width = max(w for w in WEBCAM_WIDTHS if w <= request.device.max_image_width)
    context = {
        'webcam': webcam,
        'width': width
    }
    return mobile_render(request, context, 'webcams/webcam_detail')
    
def webcam_image(request, slug, width=None):
    webcam = get_object_or_404(Webcam, slug=slug)
    
    if not width:
        data = Feed.fetch(webcam.url, category='webcam', fetch_period=webcam.fetch_period, return_data=True)
    else:
        if int(width) not in WEBCAM_WIDTHS:
            raise Http404
        Feed.fetch(webcam.url, category='webcam', fetch_period=webcam.fetch_period)
        data = open("%s-%s.jpg" % (Feed.objects.get(url=webcam.url).get_path(), width)).read()
        

    return HttpResponse(
        data,
        mimetype='image/jpg',
    )