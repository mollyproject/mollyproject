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
    (r'^adm/(.*)', admin.site.root),
    
    
    (r'^contact/', include('mobile_portal.contact.urls')),
    (r'^maps/', include('mobile_portal.maps.urls')),
    (r'^podcasts/', include('mobile_portal.podcasts.urls')),
    (r'^results/', include('mobile_portal.results.urls')),
    (r'^library/', include('mobile_portal.z3950.urls')),
    (r'^webcams/', include('mobile_portal.webcams.urls')),
    (r'^weather/', include('mobile_portal.weather.urls')),
    #(r'^auth/', include('mobile_portal.webauth.urls')),
    (r'^news/', include('mobile_portal.rss.urls')),
    (r'^osm/', include('mobile_portal.osm.urls')),
#    (r'^weblearn/', include('mobile_portal.sakai.urls')),

    (r'', include('mobile_portal.core.urls')),
)

if True or settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site-media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )

