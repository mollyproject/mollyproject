from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.osm.views',
    (r'^generated_map/(?P<hash>[a-f\d]{16})/$', 'generated_map', {}, 'osm_generated_map'),
)

