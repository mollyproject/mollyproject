from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.webauth.views',
    (r'^login/$', 'login', {}, 'auth_login'),
    (r'^logout/$', 'logout', {}, 'auth_logout'),

# Webauth
    (r'^webauth/login/$', 'webauth_login', {}, 'webauth_login'),
    (r'^webauth/logout/$', 'webauth_logout', {}, 'webauth_logout'),
    (r'^webauth/failure/$', 'webauth_failure', {}, 'webauth_failure'),
)
