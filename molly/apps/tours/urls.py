from django.conf.urls.defaults import *

from views import IndexView, CreateView, SaveView, TourView, PaperView

urlpatterns = patterns('',
    
    (r'^$',
        IndexView, {},
        'index'),
    
    (r'^(?P<slug>[a-z_\-0-9]+)/create/(?P<entities>([a-z_\-]+:[^/]+/)*)?$',
        CreateView, {},
        'create'),
    
    (r'^(?P<slug>[a-z_\-0-9]+)/create/(?P<entities>([a-z_\-]+:[^/]+/)*)save/$',
        SaveView, {},
        'save'),
    
    (r'^(?P<tour>\d+)/$',
        TourView, {},
        'tour-start'),
    
    (r'^(?P<tour>\d+)/print/$',
        PaperView, {},
        'tour-print'),
    
    (r'^(?P<tour>\d+)/(?P<page>\d+)/$',
        TourView, {},
        'tour'),
    
    )
