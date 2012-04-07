from django.conf.urls.defaults import *

from .views import (
    IndexView, UserMessageView,
    StaticDetailView, TestRunnerView
)

urlpatterns = patterns('',

    (r'^$',
        IndexView, {},
        'index'),
    
    (r'^tests$',
        TestRunnerView, {},
        'tests'),
    
    (r'^about/$',
        StaticDetailView,
        {'title':'About', 'template':'about'},
        'static_about'),

    (r'^messages/$',
        UserMessageView, {},
        'messages'),
        
)
