from django.conf.urls.defaults import *

from molly.core.views import StaticDetailView

from views import (
    IndexView,
    NearbyListView, NearbyDetailView,
    EntityDetailView,
    EntityUpdateView,

    NearbyEntityListView, NearbyEntityDetailView,
    CategoryListView, CategoryDetailView,

    BusstopSearchView, PostCodeDetailView,
    APIView,
)

urlpatterns = patterns('',
    (r'^$',
        IndexView, {},
        'index'),

    (r'^nearby/$', 
        NearbyListView, {},
        'nearby_list'),
    (r'^nearby/(?P<ptypes>[^/;]+(\;[^/;]+)*)/$',
        NearbyDetailView, {},
        'nearby_detail'),

    (r'^category/$',
        CategoryListView, {},
        'category_list'),
    (r'^category/(?P<ptypes>[^/;]+(\;[^/;]+)*)/$',
        CategoryDetailView, {},
        'category_detail'),

#    (r'^postcode:(?P<post_code>OX\d{2,3}[A-Z]{2})/((?P<ptypes>[^/;]+(\;[^/;]+)*)/)?$',
#        PostCodeDetailView, {},
#        'maps_postcode_detail'),


    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[\da-zA-Z]+)/$',
        EntityDetailView, {},
        'entity'),
    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[\da-zA-Z]+)/nearby/$',
        NearbyEntityListView, {},
        'entity_nearby_list'),
    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[\da-zA-Z]+)/nearby/(?P<ptype>[^/]+)/$',
        NearbyEntityDetailView, {},
        'entity_nearby_detail'),

    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[\da-zA-Z]+)/update/$',
        EntityUpdateView, {},
        'entity_update'),

    (r'^busstop_search/$',
        BusstopSearchView, {},
        'busstop_search'),


#    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/favourite/$',
#        'entity_favourite', {},
#        'maps_entity_favourite'),

#    (r'^without_location/$', 
#        'without_location', {},
#        'maps_without_location'),

    (r'^openstreetmap/$',
        StaticDetailView,
        {'title':'About OpenStreetMap', 'template':'openstreetmap'},
        'static_openstreetmap'),

    (r'^api/$',
        APIView, {},
        'api'),
)
