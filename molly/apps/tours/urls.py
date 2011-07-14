from django.conf.urls.defaults import *

from views import IndexView, CreateView, SaveView

urlpatterns = patterns('',
    
    (r'^$',
        IndexView, {},
        'index'),
    
    (r'^create/(?P<entities>([a-z_\-]+:[^/]+/)*)?$',
        CreateView, {},
        'create'),
    
    (r'^create/(?P<entities>([a-z_\-]+:[^/]+/)*)save/$',
        SaveView, {},
        'save'),
    
    )