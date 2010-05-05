from django.conf.urls.defaults import *

from .views import IndexView, ItemListView, ItemDetailView

urlpatterns = patterns('',
   (r'^$',
       IndexView, {},
       'events_index'),
   (r'^(?P<slug>[a-z\-]+)/$',
       ItemListView, {},
       'events_item_list'),
   (r'^(?P<slug>[a-z\-]+)/(?P<id>\d+)/$',
       ItemDetailView, {},
       'events_item_detail'),
)