from django.conf.urls.defaults import *
from views import IndexView, PodcastDetailView, CategoryDetailView, TopDownloadsView

urlpatterns = patterns('mobile_portal.podcasts.views',
    (r'^$', IndexView(), {}, 'podcasts_index'),
    (r'^(?P<code>[a-z]+)/$', CategoryDetailView(), {}, 'podcasts_category'),
    (r'^(?P<code>[a-z]+)/(?P<medium>audio|video)/$', CategoryDetailView(), {}, 'podcasts_category_medium'),
    (r'^(?P<code>[a-z]+)/(?P<id>\d+)/$', PodcastDetailView(), {}, 'podcasts_podcast'),
    (r'^top_downloads/$', TopDownloadsView(), {}, 'podcasts_top_downloads'),

    (r'^itunesu_redirect/$', 'itunesu_redirect', {}, 'podcasts_itunesu_redirect'),
)

