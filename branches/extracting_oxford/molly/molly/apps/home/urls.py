from django.conf.urls.defaults import *
from django.conf import settings

from molly.core.views import (
    IndexView, ExpositionView,
    UserMessageView,
    ExternalImageView, FeedbackView,
    StaticDetailView,
    ShortenURLView, ShortenedURLRedirectView,
)

urlpatterns = patterns('mobile_portal.core.views',

    (r'^$',
        IndexView, {},
        'index'),

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
        
    (r'^shorten_url/$',
        ShortenURLView, {},
        'shorten_url'),
    (r'^(?P<slug>[0-9][0-9A-Za-z]*)/?$',
        ShortenedURLRedirectView, {},
        'shortened_url_redirect'),
)
