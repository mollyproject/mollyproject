from django.conf.urls.defaults import *

import molly.maps.osm.urls

from views import IndexView, TouchMapLiteView

urlpatterns = patterns('',
        (r'^$', IndexView, {}, 'index'),
        (r'^touchmaplite/$', TouchMapLiteView, {}, 'touchmaplite'),
        (r'^osm/', include(molly.maps.osm.urls.urlpatterns)),
    )