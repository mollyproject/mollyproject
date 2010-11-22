from django.conf.urls.defaults import *

from molly.apps.home.views import StaticDetailView

from views import (
    IndexView,
    NearbyListView, NearbyDetailView,
    EntityDetailView,
    EntityUpdateView,

    NearbyEntityListView, NearbyEntityDetailView,
    CategoryListView, CategoryDetailView,
    
    ServiceDetailView,

    BusstopSearchView, PostCodeDetailView,
    APIView,
)

urlpatterns = patterns('',
    (r'^$',
        IndexView, {},
        'index'),

    (r'^nearby/$', 
        NearbyListView, {},
        'nearby-list'),
    (r'^nearby/(?P<ptypes>[^/;]+(\;[^/;]+)*)/$',
        NearbyDetailView, {},
        'nearby-detail'),

    (r'^category/$',
        CategoryListView, {},
        'category-list'),
    (r'^category/(?P<ptypes>[^/;]+(\;[^/;]+)*)/$',
        CategoryDetailView, {},
        'category-detail'),

#    (r'^postcode:(?P<post_code>OX\d{2,3}[A-Z]{2})/((?P<ptypes>[^/;]+(\;[^/;]+)*)/)?$',
#        PostCodeDetailView, {},
#        'maps_postcode_detail'),


    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[\da-zA-Z]+)/$',
        EntityDetailView, {},
        'entity'),
    
    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[\da-zA-Z]+)/service:(?P<service_id>.+)$',
        ServiceDetailView, {},
        'service-detail'),
    
    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[\da-zA-Z]+)/nearby/$',
        NearbyEntityListView, {},
        'entity-nearby-list'),
    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[\da-zA-Z]+)/nearby/(?P<ptype>[^/]+)/$',
        NearbyEntityDetailView, {},
        'entity-nearby-detail'),

    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[\da-zA-Z]+)/update/$',
        EntityUpdateView, {},
        'entity-update'),

    (r'^busstop_search/$',
        BusstopSearchView, {},
        'busstop-search'),


#    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/favourite/$',
#        'entity_favourite', {},
#        'maps_entity_favourite'),

#    (r'^without_location/$', 
#        'without_location', {},
#        'maps_without_location'),

    (r'^openstreetmap/$',
        StaticDetailView,
        {'title':'About OpenStreetMap', 'template':'openstreetmap'},
        'static-openstreetmap'),

    (r'^api/$',
        APIView, {},
        'api'),
)
