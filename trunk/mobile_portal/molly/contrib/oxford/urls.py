from django.conf.urls.defaults import *

from molly.conf import applications

applications.contact.urls

urlpatterns = patterns('',
    (r'^$', lambda request:None, {}, 'core_index'),
    (r'^feedback$', lambda request:None, {}, 'core_feedback'),
    (r'^shorten$', lambda request:None, {}, 'core_shorten_url'),

    (r'^contact/', include(applications.contact.urls)),
)

