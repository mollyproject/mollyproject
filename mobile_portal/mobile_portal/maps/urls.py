from django.conf.urls.defaults import *

from views import (
    IndexView,
    NearbyListView, NearbyDetailView,
    EntityDetailView,
    
    NearbyEntityListView, NearbyEntityDetailView,
    CategoryListView, CategoryDetailView,
)

urlpatterns = patterns('mobile_portal.maps.views',
    (r'^$',
        IndexView(), {},
        'maps_index'),
    
    (r'^nearby/$', 
        NearbyListView(), {},
        'maps_nearby_list'),
    (r'^nearby/(?P<ptype>[^/]+)/$',
        NearbyDetailView(), {},
        'maps_nearby_detail'),
    
    (r'^category/$',
        CategoryListView(), {},
        'maps_category_list'),
    (r'^category/(?P<ptype>[^/]+)/$',
        CategoryDetailView(), {},
        'maps_category_detail'),

    
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/$',
        EntityDetailView(), {},
        'maps_entity'),
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/nearby/$',
        NearbyEntityListView(), {},
        'maps_entity_nearby_list'),
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/nearby/(?P<ptype>[^/]+)/$',
        NearbyEntityDetailView(), {},
        'maps_entity_nearby_detail'),
    
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/favourite/$',
        'entity_favourite', {},
        'maps_entity_favourite'),

    (r'^without_location/$', 
        'without_location', {},
        'maps_without_location'),
    
)
