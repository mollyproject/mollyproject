from django.conf.urls.defaults import *
from views import (
    IndexView, PodcastDetailView, CategoryDetailView, TopDownloadsView,
    RedirectOldLinksView, ITunesURedirectView
)

urlpatterns = patterns('mobile_portal.podcasts.views',
    (r'^$',
        IndexView, {},
        'index'),
        
    (r'^division:(?P<code>[a-z]+)/$',
        CategoryDetailView, {},
        'category'),
    (r'^division:(?P<code>[a-z]+)/(?P<medium>audio|video)/$',
        CategoryDetailView, {},
        'podcasts_category_medium'),

    (r'^top_downloads/$',
        TopDownloadsView, {},
        'top_downloads'),

    (r'^itunesu_redirect/$',
        ITunesURedirectView, {},
        'itunesu_redirect'),

    (r'^(?P<code>[a-z]+)/((((?P<id>\d+)|(?P<medium>audio|video))/)?)$',
        RedirectOldLinksView, {},
        'redirects'),
        
    (r'^(?P<identifier>[a-zA-Z\d_@.\-/]+)/$',
        PodcastDetailView, {},
        'podcast'),

)

