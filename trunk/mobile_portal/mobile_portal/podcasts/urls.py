from django.conf.urls.defaults import *
from views import (
    IndexView, PodcastDetailView, CategoryDetailView, TopDownloadsView,
    RedirectOldLinksView
)

urlpatterns = patterns('mobile_portal.podcasts.views',
    (r'^$',
        IndexView, {},
        'podcasts_index'),
        
    (r'^division:(?P<code>[a-z]+)/$',
        CategoryDetailView, {},
        'podcasts_category'),
    (r'^division:(?P<code>[a-z]+)/(?P<medium>audio|video)/$',
        CategoryDetailView, {},
        'podcasts_category_medium'),

    (r'^top_downloads/$',
        TopDownloadsView, {},
        'podcasts_top_downloads'),

    (r'^(?P<code>[a-z]+)/((((?P<id>\d+)|(?P<medium>audio|video))/)?)$',
        RedirectOldLinksView, {},
        'podcasts_redirects'),
        
    (r'^(?P<identifier>[a-zA-Zd_@.\-/]+)/$',
        PodcastDetailView, {},
        'podcasts_podcast'),

    (r'^itunesu_redirect/$',
        'itunesu_redirect', {},
        'podcasts_itunesu_redirect'),
)

