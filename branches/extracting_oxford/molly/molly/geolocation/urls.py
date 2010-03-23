from django.conf.urls.defaults import *

from views import IndexView, LocationUpdateView

urlpatterns = patterns('',
    (r'^$',
        IndexView, {},
        'index'),

    (r'^update_location/$',
        LocationUpdateView, {},
        'update'),
)
    