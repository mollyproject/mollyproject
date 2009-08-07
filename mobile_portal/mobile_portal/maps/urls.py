from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('mobile_portal.maps.views',
    (r'^$', 'index', {}, 'maps_index'),
    (r'^nearest/(?P<ptype>[^/]+)/$', 'nearest', {}, 'maps_nearest'),
    (r'^nearest/(?P<ptype>.+)/(?P<distance>\d+)/$', 'nearest', {}, 'maps_nearest_distance'),
    
    (r'^oxpoints/(?P<id>\d+)/$', 'entity_detail_oxpoints', {}, 'maps_oxpoints'),
    (r'^busstop/(?P<atco_code>[\dA-Z]+)/$', 'entity_detail_busstop', {}, 'maps_busstop'),
    (r'^osm/(?P<osm_node_id>\d+)/$', 'entity_detail_osm', {}, 'maps_osm'),
#    (r'^core/update_location/$', 'mobile_portal.core.views.update_location', {}, 'core_update_location'),

    (r'^(?P<type_slug>[a-z_]+):(?P<id>[\dA-Z]+)/$', 'entity_detail', {}, 'maps_entity'),
)
