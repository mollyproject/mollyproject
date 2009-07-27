from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.sakai.views',
   (r'^$', 'index', {}, 'sakai_index'),
)