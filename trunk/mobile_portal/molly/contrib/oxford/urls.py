from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from molly.conf import applications

admin.autodiscover()

urlpatterns = patterns('',
    (r'adm/(.*)', admin.site.root),

    (r'^contact/', applications.contact.urls),
    (r'^service-status/', applications.service_status.urls),
    (r'^library/', applications.library.urls),

    (r'^search/', include('molly.googlesearch.urls', 'search', 'search')),
    (r'^maps/', include('molly.maps.urls', 'maps', 'maps')),

    (r'', include('molly.core.urls', 'core', 'core')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site-media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.SITE_MEDIA_PATH})
    )
