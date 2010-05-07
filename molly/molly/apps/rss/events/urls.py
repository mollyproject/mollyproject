from django.conf.urls.defaults import *

from .views import IndexView, ItemListView, ItemDetailView

urlpatterns = patterns('',
   (r'^$',
       IndexView, {},
       'index'),
   (r'^(?P<slug>[a-z\-]+)/$',
       ItemListView, {},
       'item_list'),
   (r'^(?P<slug>[a-z\-]+)/(?P<id>\d+)/$',
       ItemDetailView, {},
       'item_detail'),
)