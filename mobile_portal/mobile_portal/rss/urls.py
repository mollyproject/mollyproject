from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.rss.views',
   (r'^$', 'index', {}, 'rss_index'),
   (r'^(?P<slug>[a-z\-]+)/$', 'item_list', {}, 'rss_item_list'),
   (r'^(?P<slug>[a-z\-]+)/(?P<id>\d+)/$', 'item_detail', {}, 'rss_item_detail'),
)