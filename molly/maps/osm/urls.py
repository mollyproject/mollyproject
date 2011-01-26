from django.conf.urls.defaults import *

from .views import GeneratedMapView, GPXView, AboutView

urlpatterns = patterns('',
    (r'^about/$', AboutView, {}, 'osm-about'),
    (r'^generated_map/(?P<hash>[a-f\d]{16})/$', GeneratedMapView, {}, 'osm-generated_map'),
    (r'^gpx/(?P<ptype>[a-z_]+)/$', GPXView, {}, 'osm-gpx'),

)

