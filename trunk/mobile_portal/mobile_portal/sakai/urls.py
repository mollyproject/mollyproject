from django.conf.urls.defaults import *

from views import (
    IndexView, SiteView, DirectView,
    
    SignupIndexView, SignupSiteView, SignupEventView,
    
    PollIndexView, PollDetailView,
)

urlpatterns = patterns('mobile_portal.sakai.views',
   (r'^$', IndexView, {}, 'sakai_index'),
   
   (r'^signups/$',
       SignupIndexView, {},
       'sakai_signup'),
   (r'^signups/(?P<site>[^/]+)/$',
       SignupSiteView, {},
       'sakai_signup_site'),
   (r'^signups/(?P<site>[^/]+)/(?P<event_id>\d+)/$',
       SignupEventView, {},
       'sakai_signup_event'),

   (r'^polls/$',
       PollIndexView, {},
       'sakai_poll'),
   (r'^polls/(?P<id>\d+)/$',
       PollDetailView, {},
       'sakai_poll_detail'),

   (r'^sites/$', SiteView, {}, 'sakai_sites'),
   (r'^direct/$', DirectView, {}, 'sakai_direct'),
)