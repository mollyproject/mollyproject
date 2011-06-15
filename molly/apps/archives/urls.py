from django.conf.urls.defaults import *

from views import (
    IndexView,
    SearchResultView,
    ItemDetailView
)

urlpatterns = patterns('',
    (r'^$',
        IndexView, {},
        'index'),

    (r'^search/$',
        SearchResultView, {},
        'search'),

    (r'^item:(?P<resultSetPosition>\d)/$',
        ItemDetailView, {},
        'item-detail'),
)
