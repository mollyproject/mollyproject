from django.conf.urls.defaults import *

from .views import (
    IndexView, UserMessageView,
    StaticDetailView,
)

urlpatterns = patterns('',

    (r'^$',
        IndexView, {},
        'index'),

#    (r'^customise/$', 'customise', {}, 'core_customise'),
#    (r'^customise/location_sharing/$',
#        'location_sharing', {},
#        'core_location_sharing'),
    
    (r'^about/$',
        StaticDetailView,
        {'title':'About', 'template':'about'},
        'static_about'),

    (r'^messages/$',
        UserMessageView, {},
        'messages'),
        
)
