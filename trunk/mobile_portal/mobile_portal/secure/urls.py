from django.conf.urls.defaults import *

from views import IndexView, ClearSessionView

urlpatterns = patterns('',
    (r'^$',
        IndexView, {},
        'secure_index'),
        
    (r'^clear-session/$',
        ClearSessionView, {},
        'secure_clear_session'),
)