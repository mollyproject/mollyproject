from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.webcams.views',
    (r'^$', 'index', {}, 'webcams_index'),
    (r'^(?P<slug>[a-zA-Z0-9\-]+)/$', 'webcam_detail', {}, 'webcams_webcam'),
)

