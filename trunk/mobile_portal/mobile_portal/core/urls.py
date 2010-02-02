from django.conf.urls.defaults import *
from django.conf import settings

from mobile_portal.core.views import (
    IndexView, LocationUpdateView, ExpositionView,
    UserMessageView,
    ExternalImageView, RunCommandView, FeedbackView,
    StaticDetailView,
    ShortenURLView, ShortenedURLRedirectView,
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
    
    (r'^desktop/((?P<page>features|accessing|get-involved|blog|help)/)?$',
        ExpositionView, {},
        'core_exposition'),

    (r'^feedback/$',
        FeedbackView, {},
        'core_feedback'),

    (r'^messages/$',
        UserMessageView, {},
        'core_messages'),
        
    (r'^shorten_url/$',
        ShortenURLView, {},
        'core_shorten_url'),
    (r'^(?P<slug>[0-9][0-9A-Za-z]*)/?$',
        ShortenedURLRedirectView, {},
        'core_shortened_url_redirect'),
)
