from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('mobile_portal.podcasts.views',
    # Example:
    # (r'^mobile_portal/', include('mobile_portal.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
    (r'^$', 'index', {}, 'podcasts_index'),
    (r'^(?P<code>[a-z]+)/$', 'category_detail', {}, 'podcasts_category'),
    (r'^(?P<code>[a-z]+)/(?P<medium>audio|video)/$', 'category_detail', {}, 'podcasts_category_medium'),
    (r'^(?P<code>[a-z]+)/(?P<id>\d+)/$', 'podcast_detail', {}, 'podcasts_podcast'),
    (r'^top_downloads/$', 'top_downloads', {}, 'podcasts_top_downloads'),
)

