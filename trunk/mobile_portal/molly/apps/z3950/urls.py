from django.conf.urls.defaults import *

from molly.apps.z3950.views import (
    IndexView, SearchDetailView,
    ItemDetailView, ItemHoldingsView,
)

urlpatterns = patterns('mobile_portal.z3950.views',
    (r'^$',
        IndexView, {},
        'index'),
    (r'^search/$',
        SearchDetailView, {},
        'search'),

    (r'^item:(?P<control_number>\d{8})/$',
        ItemDetailView, {},
        'item_detail'),
    (r'^item:(?P<control_number>\d{8})/(?P<sublocation>.+)/$',
        ItemHoldingsView, {},
        'item_holdings_detail'),
)
