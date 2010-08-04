from django.conf.urls.defaults import *

from views import IndexView, ClearHistoryView

urlpatterns = patterns('',
    (r'^$',
        IndexView, {},
        'index'),

    (r'^clear/$',
        ClearHistoryView, {},
        'clear'),

)
    