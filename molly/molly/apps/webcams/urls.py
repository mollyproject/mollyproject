from django.conf.urls.defaults import *

from views import IndexView, WebcamDetailView

urlpatterns = patterns('',
    (r'^$', IndexView, {}, 'index'),
    (r'^(?P<slug>[a-zA-Z0-9\-]+)/$', WebcamDetailView, {}, 'webcam'),
)

