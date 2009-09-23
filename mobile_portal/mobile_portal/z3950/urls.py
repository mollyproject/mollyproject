from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.z3950.views',
    (r'^$', 'index', {}, 'z3950_index'),

    (r'^isbn/$', 'search_isbn', {}, 'z3950_isbn'),
    (r'^isbn/(?P<isbn>\d{9,12}[\dX])/$', 'search_isbn', {}, 'z3950_isbn_detail'),

    (r'^item/(?P<control_number>\d{8})/$', 'item_detail', {}, 'z3950_item_detail'),
)
