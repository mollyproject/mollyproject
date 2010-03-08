from django.conf.urls.defaults import *

from .views import (
    IndexView, SiteView, DirectView,
    
    SignupIndexView, SignupSiteView, SignupEventView,
    
    PollIndexView, PollDetailView,
)

urlpatterns = patterns('mobile_portal.sakai.views',
    (r'^$',
        IndexView, {},
        'index'),

    (r'^signups/$',
        SignupIndexView, {},
        'signup'),
    (r'^signups/(?P<site>[^/]+)/$',
        SignupSiteView, {},
        'signup_site'),
    (r'^signups/(?P<site>[^/]+)/(?P<event_id>\d+)/$',
        SignupEventView, {},
        'signup_event'),

    (r'^polls/$',
        PollIndexView, {},
        'poll'),
    (r'^polls/(?P<id>\d+)/$',
        PollDetailView, {},
        'poll_detail'),

    (r'^sites/$', SiteView, {}, 'sites'),
    (r'^direct/$', DirectView, {}, 'direct'),
)
