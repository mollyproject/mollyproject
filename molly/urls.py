from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from djcelery.models import PeriodicTask

from molly.conf.admin import RunnablePeriodicTaskAdmin
from molly.conf import applications, all_apps
from molly.utils.views import ReverseView
from molly.utils.i18n import SetLanguageView, javascript_catalog

# Admin
admin.autodiscover()
admin.site.unregister(PeriodicTask)
admin.site.register(PeriodicTask, RunnablePeriodicTaskAdmin)

urlpatterns = patterns('',
    (r'^adm/', include(admin.site.urls)), # Admin site
    (r'^comments/', include('django.contrib.comments.urls')), # Django comments
    (r'', applications.home.urls), # Home default
    (r'^reverse', ReverseView, {}, 'reverse'),
    (r'^set-language/$', SetLanguageView, {}, 'set-language'), # Change language view
    (r'^jsi18n/$', javascript_catalog,
     {'packages': settings.INSTALLED_APPS}, 'js-i18n')) # JS i18n catalogues

# Dynamically add apps
for app in (app for app in all_apps() if app.has_urlconf and app.local_name != 'home'):
    urlpatterns += patterns('',
        (r'^' + app.local_name + '/', include(app.urls)))

# Redirecting old URLs
urlpatterns += patterns('django.views.generic.simple',
    (r'^maps/busstop:(?P<atco>[A-Z\d]+)/(?P<remain>.*)$', 'redirect_to', {'url': '/places/atco:%(atco)s/%(remain)s'}),
    (r'^maps/[a-z]\-+:(?P<id>\d{8})/(?P<remain>.*)$', 'redirect_to', {'url': '/places/oxpoints:%(id)s/%(remain)s'}),
    (r'^maps/[a-z]\-+:(?P<id>[NW]\d{8})/(?P<remain>.*)$', 'redirect_to', {'url': '/places/osm:%(id)s/%(remain)s'}),
    (r'^maps/(?P<remain>.*)$', 'redirect_to', {'url': '/places/%(remain)s'}),
    (r'^osm/(?P<remain>.*)$', 'redirect_to', {'url': '/maps/osm/%(remain)s'}),
)

handler500 = 'molly.utils.views.handler500'

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT})
    )
