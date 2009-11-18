from django.conf.urls.defaults import *

from views import IndexView, SignupView, SiteView

urlpatterns = patterns('mobile_portal.sakai.views',
   (r'^$', IndexView(), {}, 'sakai_index'),
   
   (r'^signups/$',
       SignupView(), {},
       'sakai_signup'),
   (r'^signups/(?P<site>[^/]+)/$',
       SignupView(), {},
       'sakai_signup_site'),
   (r'^signups/(?P<site>[^/]+)/(?P<event_id>\d+)/$',
       SignupView(), {},
       'sakai_signup_event'),

   (r'^sites/$', SiteView(), {}, 'sakai_sites'),
)