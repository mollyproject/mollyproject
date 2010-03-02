from django.conf.urls.defaults import *

from .views import MetadataView

urlpatterns = patterns('molly.osm.views',
    (r'^generated_map/(?P<hash>[a-f\d]{16})/$', 'generated_map', {}, 'osm_generated_map'),

    (r'^metadata/(?P<ptype>[a-z_]+)/$', MetadataView, {}, 'osm_metadata'),
)

