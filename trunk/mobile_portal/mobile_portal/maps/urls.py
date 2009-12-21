from django.conf.urls.defaults import *

from mobile_portal.core.views import StaticDetailView

from views import (
    IndexView,
    NearbyListView, NearbyDetailView,
    EntityDetailView,
    EntityUpdateView,
    
    NearbyEntityListView, NearbyEntityDetailView,
    CategoryListView, CategoryDetailView,
    
    BusstopSearchView, PostCodeDetailView
)

urlpatterns = patterns('mobile_portal.maps.views',
    (r'^$',
        IndexView, {},
        'maps_index'),
    
    (r'^nearby/$', 
        NearbyListView, {},
        'maps_nearby_list'),
    (r'^nearby/(?P<ptypes>[^/;]+(\;[^/;]+)*)/$',
        NearbyDetailView, {},
        'maps_nearby_detail'),
    
    (r'^category/$',
        CategoryListView, {},
        'maps_category_list'),
    (r'^category/(?P<ptypes>[^/;]+(\;[^/;]+)*)/$',
        CategoryDetailView, {},
        'maps_category_detail'),

#    (r'^postcode:(?P<post_code>OX\d{2,3}[A-Z]{2})/((?P<ptypes>[^/;]+(\;[^/;]+)*)/)?$',
#        PostCodeDetailView, {},
#        'maps_postcode_detail'),
    
    
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/$',
        EntityDetailView, {},
        'maps_entity'),
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/nearby/$',
        NearbyEntityListView, {},
        'maps_entity_nearby_list'),
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/nearby/(?P<ptype>[^/]+)/$',
        NearbyEntityDetailView, {},
        'maps_entity_nearby_detail'),

    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/update/$',
        EntityUpdateView, {},
        'maps_entity_update'),
        
    (r'^busstop_search/$',
        BusstopSearchView, {},
        'maps_busstop_search'),
        
    
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/favourite/$',
        'entity_favourite', {},
        'maps_entity_favourite'),

    (r'^without_location/$', 
        'without_location', {},
        'maps_without_location'),
    
    (r'^openstreetmap/$',
        StaticDetailView,
        {'title':'About OpenStreetMap', 'template':'openstreetmap'},
        'maps_static_openstreetmap'),
   
)
