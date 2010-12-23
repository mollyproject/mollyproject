from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    
    (r'^popular-pages$',
        PopularPagesView, {},
        'popular-pages'),
    
    (r'^popular-404s$',
        Popular404sView, {},
        'popular-404s'),
    
    (r'^slow-pages$',
        SlowPagesView, {},
        'slow-pages'),
    
    (r'^popular-devices$',
        PopularDevicesView, {},
        'popular-devices'),
    
    (r'^$',
        IndexView, {},
        'index'),
    
    )