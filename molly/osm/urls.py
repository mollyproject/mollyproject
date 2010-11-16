from django.conf.urls.defaults import *

from .views import GeneratedMapView, MetadataView, GPXView, AboutView, IndexView

urlpatterns = patterns('',
    (r'^$', IndexView, {}, 'index'),
    (r'^about/$', AboutView, {}, 'about'),
    (r'^generated_map/(?P<hash>[a-f\d]{16})/$', GeneratedMapView, {}, 'generated_map'),

    (r'^metadata/(?P<ptype>[a-z_]+)/$', MetadataView, {}, 'metadata'),
    (r'^gpx/(?P<ptype>[a-z_]+)/$', GPXView, {}, 'gpx'),

)

