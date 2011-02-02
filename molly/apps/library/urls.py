from django.conf.urls.defaults import *

from views import (
    IndexView, SearchDetailView,
    ItemDetailView, ItemHoldingsView,
)

urlpatterns = patterns('',
    (r'^$',
        IndexView, {},
        'index'),
    (r'^search/$',
        SearchDetailView, {},
        'search'),

    (r'^item:(?P<control_number>[^/]+)/$',
        ItemDetailView, {},
        'item-detail'),
    (r'^item:(?P<control_number>[^/]+)/(?P<sublocation>.+)/$',
        ItemHoldingsView, {},
        'item-holdings-detail'),
)
