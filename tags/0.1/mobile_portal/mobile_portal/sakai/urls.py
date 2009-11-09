from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.sakai.views',
   (r'^$', 'index', {}, 'sakai_index'),
   (r'^signup/$', 'signup_index', {}, 'sakai_signup'),
   (r'^signup/(?P<site_id>[a-f\d]{8}):(?P<meeting>\d{12}):(?P<timeslot>\d{12})/$', 'signup_timeslot', {}, 'sakai_signup_timeslot'),

   (r'^set_cookie/$', 'set_cookie', {}, 'sakai_set_cookie'),
)