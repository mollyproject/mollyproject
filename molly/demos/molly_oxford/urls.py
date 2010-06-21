from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from molly.conf import applications

admin.autodiscover()

urlpatterns = patterns('',
    (r'^adm/(.*)', admin.site.root),

    # These are how we expect all applications to be eventually.
    (r'^contact/', applications.contact.urls),
    (r'^service-status/', applications.service_status.urls),
    (r'^weather/', applications.weather.urls),
    (r'^library/', applications.library.urls),
    (r'^podcasts/', applications.podcasts.urls),
    (r'^webcams/', applications.webcams.urls),
    (r'^results/', applications.results.urls),
    (r'^search/', applications.search.urls),
    (r'^geolocation/', applications.geolocation.urls),
    (r'^places/', applications.places.urls),
    (r'^feedback/', applications.feedback.urls),
    (r'^news/', applications.news.urls),
    (r'^external-media/', applications.external_media.urls),
    (r'^device-detection/', applications.device_detection.urls),
    (r'^osm/', applications.osm.urls),
    (r'', applications.home.urls),

#    (r'^auth/', applications.auth.urls),
#    (r'^weblearn/', applications.weblearn.urls),
#    (r'^url-shortener/', applications.url_shortener.urls),
#    (r'^events/', applications.events.urls),

    # These ones still need work

)

# Redirecting old URLs
urlpatterns += patterns('django.views.generic.simple',
    (r'^maps/busstop:(?P<atco>[A-Z\d]+)/(?P<remain>.*)$', 'redirect_to', {'url': '/places/atco:%(atco)s/%(remain)s'}),
    (r'^maps/[a-z]\-+:(?P<id>\d{8})/(?P<remain>.*)$', 'redirect_to', {'url': '/places/oxpoints:%(id)s/%(remain)s'}),
    (r'^maps/[a-z]\-+:(?P<id>[NW]\d{8})/(?P<remain>.*)$', 'redirect_to', {'url': '/places/osm:%(id)s/%(remain)s'}),
    (r'^maps/(?P<remain>.*)$', 'redirect_to', {'url': '/places/%(remain)s'}),
)


handler500 = 'molly.apps.home.views.handler500'

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site-media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.SITE_MEDIA_PATH})
    )
