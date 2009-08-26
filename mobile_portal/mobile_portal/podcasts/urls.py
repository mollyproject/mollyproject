from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.podcasts.views',
    (r'^$', 'index', {}, 'podcasts_index'),
    (r'^(?P<code>[a-z]+)/$', 'category_detail', {}, 'podcasts_category'),
    (r'^(?P<code>[a-z]+)/(?P<medium>audio|video)/$', 'category_detail', {}, 'podcasts_category_medium'),
    (r'^(?P<code>[a-z]+)/(?P<id>\d+)/$', 'podcast_detail', {}, 'podcasts_podcast'),
    (r'^top_downloads/$', 'top_downloads', {}, 'podcasts_top_downloads'),

    (r'^itunesu_redirect/$', 'itunesu_redirect', {}, 'podcasts_itunesu_redirect'),
)

