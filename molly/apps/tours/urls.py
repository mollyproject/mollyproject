from django.conf.urls.defaults import *

from views import TourView

urlpatterns = patterns('',
    
    (r'^(?P<entities>([a-z_\-]+:[^/]+/)*)$',
        TourView, {},
        'index'),
    
    )