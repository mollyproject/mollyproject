from django.conf.urls.defaults import *
from django.conf import settings

from django.http import HttpResponsePermanentRedirect
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
    # (r'^molly/', include('mobile_portal.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^adm/(.*)', admin.site.root),
    
    
    (r'^contact/', include('molly.contact.urls')),
    (r'^maps/', include('molly.maps.urls')),
    (r'^podcasts/', include('molly.podcasts.urls')),
    (r'^results/', include('molly.results.urls')),
    (r'^library/', include('molly.z3950.urls')),
    (r'^webcams/', include('molly.webcams.urls')),
    (r'^weather/', include('molly.weather.urls')),
    #(r'^auth/', include('molly.webauth.urls')),
    
    (r'^news/', include('molly.rss.news.urls')),
    (r'^events/', include('molly.rss.events.urls')),
    
    (r'^osm/', include('molly.osm.urls')),
    (r'^search/', include('molly.googlesearch.urls')),
    (r'^secure/', include('molly.secure.urls')),
    (r'^weblearn/', include('molly.sakai.urls')),
    (r'^service-status/', include('molly.service_status.urls')),

    (r'', include('molly.core.urls')),
    
    # We've moved oucs-status to service-status, so we'd better keep people informed
    (r'^oucs-status/', app_moved('/oucs-status/', '/service-status/')),
    (r'^desktop_about/', app_moved('/desktop_about/', '/desktop/')),
)

handler500 = 'molly.core.views.handler500'

if True or settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^site-media/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )

