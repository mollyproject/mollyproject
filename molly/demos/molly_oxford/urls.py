from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from molly.conf import applications

admin.autodiscover()

urlpatterns = patterns('',
    (r'adm/(.*)', admin.site.root),

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
    (r'', applications.home.urls),

#    (r'^auth/', applications.auth.urls),
#    (r'^url-shortener/', applications.url_shortener.urls),
#    (r'^weblearn/', applications.weblearn.urls),
#    (r'^events/', applications.events.urls),

    # These ones still need work

    (r'^osm/', include('molly.osm.urls', 'osm', 'osm')),

    # This one shouldn't be shown yet, but the home view chokes if 
    # the namespace isn't known

)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site-media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.SITE_MEDIA_PATH})
    )
