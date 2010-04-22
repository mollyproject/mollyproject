from django.conf.urls.defaults import *

from views import (
    IndexView, ExpositionView, UserMessageView,
    FeedbackView, StaticDetailView,
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
    
    (r'^desktop/((?P<page>features|accessing|get-involved|blog|help)/)?$',
        ExpositionView, {},
        'exposition'),

    (r'^feedback/$',
        FeedbackView, {},
        'feedback'),

    (r'^messages/$',
        UserMessageView, {},
        'messages'),
        
)
