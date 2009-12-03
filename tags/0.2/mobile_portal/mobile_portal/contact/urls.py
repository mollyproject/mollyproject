from django.conf.urls.defaults import *

from views import IndexView

urlpatterns = patterns('mobile_portal.contact.views',
    (r'^$', IndexView, {}, 'contact_index'),
#    (r'^quick/$', 'quick_contacts', {}, 'contact_quick'),
)
