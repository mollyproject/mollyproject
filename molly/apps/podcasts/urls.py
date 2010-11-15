from django.conf.urls.defaults import *
from views import (
    IndexView, PodcastDetailView, CategoryDetailView,
    ITunesURedirectView
)

urlpatterns = patterns('',
    (r'^$',
        IndexView, {},
        'index'),
        
    (r'^category:(?P<category>[\dA-Z\-a-z]+)/$',
        CategoryDetailView, {},
        'category'),
    (r'^category:(?P<category>[\dA-Z\-a-z]+)/(?P<medium>[a-z]+)/$',
        CategoryDetailView, {},
        'category-medium'),

    (r'^itunesu_redirect/$',
        ITunesURedirectView, {},
        'itunesu-redirect'),

    (r'^(?P<slug>[a-zA-Z\d_@.\-/]+)/$',
        PodcastDetailView, {},
        'podcast'),

)

