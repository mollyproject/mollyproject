from django.conf.urls.defaults import *

import molly.maps.osm.urls

from views import IndexView

urlpatterns = patterns('',
        (r'^$', IndexView, {}, 'index'),
        (r'^osm/', include(molly.maps.osm.urls.urlpatterns)),
    )