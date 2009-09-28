from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('mobile_portal.core.views',

    (r'^$', 'index', {}, 'core_index'),
    (r'^ajax/update_location/$', 'ajax_update_location', {}, 'core_ajax_update_location'),
    (r'^update_location/$', 'update_location', {}, 'core_update_location'),
    (r'^core/run_command/$', 'run_command', {}, 'core_run_command'),
    (r'^external_images/(?P<slug>[0-9a-f]{8})/$', 'external_image', {}, 'external_image'),

    (r'^customise/$', 'customise', {}, 'core_customise'),
    (r'^customise/location_sharing/$', 'location_sharing', {}, 'core_location_sharing'),
    
    (r'^about/$', 'static_detail', {'title':'About', 'template':'about'}, 'core_static_about'),
)
