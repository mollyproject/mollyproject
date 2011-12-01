from django.conf.urls.defaults import *

from molly.apps.home.views import StaticDetailView

from views import (
    IndexView,
    NearbyListView, NearbyDetailView,
    EntityDetailView,
    EntityUpdateView,
    RouteView,

    NearbyEntityListView, NearbyEntityDetailView,
    CategoryListView, CategoryDetailView,
    
    ServiceDetailView, EntityDirectionsView, TimetableView,
)

urlpatterns = patterns('',
    (r'^$',
        IndexView, {},
        'index'),

    (r'^nearby/$', 
        NearbyListView, {},
        'nearby-list'),
    (r'^nearby/(?P<ptypes>[^/;]+(\;[^/;]+)*)/$',
        NearbyDetailView, {},
        'nearby-detail'),

    (r'^category/$',
        CategoryListView, {},
        'category-list'),
    (r'^category/(?P<ptypes>[^/;]+(\;[^/;]+)*)/$',
        CategoryDetailView, {},
        'category-detail'),

    (r'^route:(?P<route>[^/]+)/(?P<id>\d+)?$',
        RouteView, {},
        'route'),

    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[^/]+)/$',
        EntityDetailView, {},
        'entity'),
    
    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[^/]+)/directions/$',
        EntityDirectionsView, {},
        'entity-directions'),
    
    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[^/]+)/service$',
        ServiceDetailView, {},
        'service-detail'),
    
    #(r'^(?P<scheme>[a-z_\-]+):(?P<value>[^/]+)/timetable/((?P<year>\d{4})\-(?P<month>\d{2})\-(?P<day>\d{2})/)?$',
    #    TimetableView, {},
    #    'timetable'),
    
    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[^/]+)/nearby/$',
        NearbyEntityListView, {},
        'entity-nearby-list'),
    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[^/]+)/nearby/(?P<ptype>[^/]+)/$',
        NearbyEntityDetailView, {},
        'entity-nearby-detail'),

    (r'^(?P<scheme>[a-z_\-]+):(?P<value>[^/]+)/update/$',
        EntityUpdateView, {},
        'entity-update'),

    (r'^openstreetmap/$',
        StaticDetailView,
        {'title':'About OpenStreetMap', 'template':'openstreetmap'},
        'static-openstreetmap'),
)
