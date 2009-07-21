from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('mobile_portal.maps.views',
    (r'^$', 'index', {}, 'maps_index'),
    (r'^nearest/(?P<ptype>.+)/$', 'nearest', {}, 'maps_nearest'),
    
    (r'^oxpoints/(?P<id>\d+)/$', 'oxpoints', {}, 'maps_oxpoints'),
#    (r'^core/update_location/$', 'mobile_portal.core.views.update_location', {}, 'core_update_location'),

)
