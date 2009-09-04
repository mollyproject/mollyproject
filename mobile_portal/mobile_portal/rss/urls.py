from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.rss.views',
   (r'^$', 'index', {}, 'rss_index'),
   (r'^(?P<slug>[a-z\-]+)/$', 'feed_detail', {}, 'rss_feed_detail'),
   (r'^manage/$', 'manage', {}, 'rss_manage'),
   (r'^feed_display/$', 'feed_display', {}, 'rss_feed_display'),
)