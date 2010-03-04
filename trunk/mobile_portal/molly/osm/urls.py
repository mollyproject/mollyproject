from django.conf.urls.defaults import *

from .views import MetadataView, GPXView

urlpatterns = patterns('molly.osm.views',
    (r'^generated_map/(?P<hash>[a-f\d]{16})/$', 'generated_map', {}, 'osm_generated_map'),

    (r'^metadata/(?P<ptype>[a-z_]+)/$', MetadataView, {}, 'osm_metadata'),
    (r'^gpx/(?P<ptype>[a-z_]+)/$', GPXView, {}, 'osm_gpx'),

)

