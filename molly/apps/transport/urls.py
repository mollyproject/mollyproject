from django.conf.urls.defaults import *

from views import (IndexView, RailView, TravelNewsView, ParkAndRideView,
                   PublicTransportView, RoutesView)

urlpatterns = patterns('',
   (r'^$', IndexView, {}, 'index'),
   (r'^rail/$', RailView, {}, 'rail'),
   (r'^travel-news/$', TravelNewsView, {}, 'travel-news'),
   (r'^park-and-ride/$', ParkAndRideView, {}, 'park-and-ride'),
   (r'^(?P<key>[^/]+)/$', PublicTransportView, {}, 'public-transport'),
   (r'^(?P<key>[^/]+)/routes/$', RoutesView, {}, 'routes'),
)
