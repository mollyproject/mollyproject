from django.conf.urls.defaults import *

from .views import IndexView, ItemListView, ItemDetailView

urlpatterns = patterns('',
   (r'^$',
       IndexView, {},
       'news_index'),
   (r'^(?P<slug>[a-z\-]+)/$',
       ItemListView, {},
       'news_item_list'),
   (r'^(?P<slug>[a-z\-]+)/(?P<id>\d+)/$',
       ItemDetailView, {},
       'news_item_detail'),
)