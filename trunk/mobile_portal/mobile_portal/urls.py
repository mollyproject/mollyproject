from django.conf.urls.defaults import *
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

from django.http import HttpResponsePermanentRedirect

def app_moved(old, new):
    def f(request):
        return HttpResponsePermanentRedirect(
            new+request.get_full_path()[len(old):]
        )
    return f

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
    
    (r'^news/', include('mobile_portal.rss.news.urls')),
    (r'^events/', include('mobile_portal.rss.events.urls')),
    
    (r'^osm/', include('mobile_portal.osm.urls')),
    (r'^search/', include('mobile_portal.googlesearch.urls')),
    (r'^secure/', include('mobile_portal.secure.urls')),
    (r'^weblearn/', include('mobile_portal.sakai.urls')),
    (r'^service-status/', include('mobile_portal.service_status.urls')),

    (r'', include('mobile_portal.core.urls')),
    
    # We've moved oucs-status to service-status, so we'd better keep people informed
    (r'^oucs-status/', app_moved('/oucs-status/', '/service-status/')),
)

handler500 = 'mobile_portal.core.views.handler500'

if True or settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^site-media/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )

