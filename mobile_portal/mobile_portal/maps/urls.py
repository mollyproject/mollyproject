from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('mobile_portal.maps.views',
    (r'^$',
        'index', {},
        'maps_index'),
    
    (r'^nearby/$', 
        'nearby_list', {},
        'maps_nearby_list'),
    (r'^nearby/(?P<ptype>[^/]+)/$',
        'nearby_detail', {},
        'maps_nearby_detail'),
    
    (r'^category/$',
        'category_list', {},
        'maps_category_list'),
    (r'^category/(?P<ptype>[^/]+)/$',
        'category_detail', {},
        'maps_category_detail'),

    
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/$',
        'entity_detail', {},
        'maps_entity'),
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/nearby/$',
        'entity_nearby_list', {},
        'maps_entity_nearby_list'),
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/nearby/(?P<ptype>[^/]+)/$',
        'entity_nearby_detail', {},
        'maps_entity_nearby_detail'),
    
    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/favourite/$',
        'entity_favourite', {},
        'maps_entity_favourite'),
    
)
