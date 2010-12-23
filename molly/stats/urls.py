from django.conf.urls.defaults import *

from views import IndexView, SlowPagesView

urlpatterns = patterns('',
    (r'^slow-pages$',
        SlowPagesView, {},
        'slow-pages'),
    
    (r'^$',
        IndexView, {},
        'index'),
    )