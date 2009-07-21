from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('mobile_portal.webcams.views',
    # Example:
    # (r'^mobile_portal/', include('mobile_portal.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
    (r'^$', 'index', {}, 'webcams_index'),
    (r'^(?P<slug>[a-zA-Z0-9\-]+)/$', 'webcam_detail', {}, 'webcams_webcam'),
    (r'^(?P<slug>[a-zA-Z0-9\-]+)/image/$', 'webcam_image', {}, 'webcams_image'),
    (r'^(?P<slug>[a-zA-Z0-9\-]+)/image/(?P<width>\d{3})/$', 'webcam_image', {}, 'webcams_image_width'),
)

