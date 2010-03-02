from django.conf.urls.defaults import *
from django.conf import settings

from molly.conf import applications

applications.contact.urls

urlpatterns = patterns('',
    (r'^$', lambda request:None, {}, 'core_index'),
    (r'^feedback$', lambda request:None, {}, 'core_feedback'),
    (r'^shorten$', lambda request:None, {}, 'core_shorten_url'),

    (r'^contact/', include(applications.contact.urls)),
    (r'^service-status/', include(applications.service_status.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site-media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.SITE_MEDIA_PATH})
    )
