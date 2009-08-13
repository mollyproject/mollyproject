from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.rss.views',
   (r'^$', 'index', {}, 'rss_index'),
)