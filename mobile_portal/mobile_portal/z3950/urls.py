from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.z3950.views',
    (r'^$', 'index', {}, 'z3950_index'),
    (r'^search/$', 'search_detail', {}, 'z3950_search'),

    (r'^item/(?P<control_number>\d{8})/$', 'item_detail', {}, 'z3950_item_detail'),
    (r'^item/(?P<control_number>\d{8})/(?P<sublocation>[^\/])/$', 'item_holdings_detail', {}, 'z3950_item_holdings_detail'),
)
