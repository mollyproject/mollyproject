from django.conf.urls.defaults import *
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^mobile_portal/', include('mobile_portal.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),


    (r'^crisis/$', 'mobile_portal.core.views.crisis', {}, 'core_crisis'),
    (r'^contact/', include('mobile_portal.contact.urls')),
    (r'^maps/', include('mobile_portal.maps.urls')),
    (r'^podcasts/', include('mobile_portal.podcasts.urls')),
    (r'^results/', include('mobile_portal.results.urls')),
    (r'^webcams/', include('mobile_portal.webcams.urls')),
    (r'^auth/', include('mobile_portal.webauth.urls')),

    (r'', include('mobile_portal.core.urls')),
)

if False and settings.DEBUG:
    urlpatterns += patterns('',
        (r'^ste-media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )

