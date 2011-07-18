from django.conf.urls.defaults import *

from views import IndexView, CreateView, SaveView, TourView

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
    
    (r'^(?P<tour>\d+)/$',
        TourView, {},
        'tour-start'),
    
    (r'^(?P<tour>\d+)/(?P<page>\d+)/$',
        TourView, {},
        'tour'),
    
    )