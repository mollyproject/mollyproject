from django.conf.urls.defaults import *

from views import IndexView

urlpatterns = patterns('',
    
    (r'^(?P<entities>([a-z_\-]+:[^/]+/)*)$',
        IndexView, {},
        'index'),
    
    )