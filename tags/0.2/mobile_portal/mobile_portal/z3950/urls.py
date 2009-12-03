from django.conf.urls.defaults import *

from mobile_portal.z3950.views import (
    IndexView, SearchDetailView,
    ItemDetailView, ItemHoldingsView,
)

urlpatterns = patterns('mobile_portal.z3950.views',
    (r'^$',
        IndexView, {},
        'z3950_index'),
    (r'^search/$',
        SearchDetailView, {},
        'z3950_search'),

    (r'^item:(?P<control_number>\d{8})/$',
        ItemDetailView, {},
        'z3950_item_detail'),
    (r'^item:(?P<control_number>\d{8})/(?P<sublocation>.+)/$',
        ItemHoldingsView, {},
        'z3950_item_holdings_detail'),
)
