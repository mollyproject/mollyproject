from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('mobile_portal.maps.views',
    (r'^$', 'index', {}, 'maps_index'),
    (r'^nearest/(?P<ptype>[^/]+)/$', 'nearest', {}, 'maps_nearest'),
    (r'^nearest/(?P<ptype>.+)/(?P<distance>\d+)/$', 'nearest', {}, 'maps_nearest_distance'),
    
    (r'^oxpoints/(?P<id>\d+)/$', 'oxpoints_entity', {}, 'maps_oxpoints'),
    (r'^busstop/(?P<atco_code>[\dA-Z]+)/$', 'busstop', {}, 'maps_busstop'),
    (r'^osm/(?P<osm_node_id>\d+)/$', 'osm', {}, 'maps_osm'),
#    (r'^core/update_location/$', 'mobile_portal.core.views.update_location', {}, 'core_update_location'),

)
