from django.conf.urls.defaults import *

from views import IndexView, ItemListView, ItemDetailView

urlpatterns = patterns('',
   (r'^$', IndexView(), {}, 'rss_index'),
   (r'^(?P<slug>[a-z\-]+)/$', ItemListView(), {}, 'rss_item_list'),
   (r'^(?P<slug>[a-z\-]+)/(?P<id>\d+)/$', ItemDetailView(), {}, 'rss_item_detail'),
)