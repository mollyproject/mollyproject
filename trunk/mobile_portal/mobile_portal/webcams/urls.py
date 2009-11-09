from django.conf.urls.defaults import *

from views import IndexView, WebcamDetailView

urlpatterns = patterns('mobile_portal.webcams.views',
    (r'^$', IndexView(), {}, 'webcams_index'),
    (r'^(?P<slug>[a-zA-Z0-9\-]+)/$', WebcamDetailView(), {}, 'webcams_webcam'),
)

