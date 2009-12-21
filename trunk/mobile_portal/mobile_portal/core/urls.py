from django.conf.urls.defaults import *
from django.conf import settings

from mobile_portal.core.views import (
    IndexView, LocationUpdateView, DesktopAboutView,
    UserMessageView,
    ExternalImageView, RunCommandView, FeedbackView,
    StaticDetailView
)

urlpatterns = patterns('mobile_portal.core.views',

    (r'^$',
        IndexView, {},
        'core_index'),
        
    (r'^update_location/$',
        LocationUpdateView, {},
        'core_update_location'),

    (r'^core/run_command/$',
        RunCommandView, {},
        'core_run_command'),

    (r'^external_images/(?P<slug>[0-9a-f]{8})/$',
        ExternalImageView, {},
        'external_image'),

#    (r'^customise/$', 'customise', {}, 'core_customise'),
#    (r'^customise/location_sharing/$',
#        'location_sharing', {},
#        'core_location_sharing'),
    
    (r'^about/$',
        StaticDetailView,
        {'title':'About', 'template':'about'},
        'core_static_about'),
    
    (r'^desktop_about/$',
        DesktopAboutView, {},
        'core_desktop_about'),

    (r'^feedback/$',
        FeedbackView, {},
        'core_feedback'),

    (r'^messages/$',
        UserMessageView, {},
        'core_messages'),
)
