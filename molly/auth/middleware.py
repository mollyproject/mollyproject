import time, random

from django.conf import settings
from django.utils.cache import patch_vary_headers
from django.utils.http import cookie_date
from django.utils.importlib import import_module
from django.http import HttpResponsePermanentRedirect, HttpResponseForbidden
from django.contrib.auth.models import User

from .views import SecureView
from .models import UserSession
from molly.utils.views import BaseView

class SecureSessionMiddleware(object):
    def process_request(self, request):
        if request.is_secure() or settings.DEBUG_SECURE:
            engine = import_module(settings.SESSION_ENGINE)
            secure_session_key = request.COOKIES.get('secure_session_id', None)
            request.secure_session = engine.SessionStore(secure_session_key)
            
            # If this is a new session, mark it as being secure so we can
            # refuse requests where session keys have been swapped about.
            if secure_session_key is None:
                request.secure_session['is_secure'] = True

            secure_session_key = request.secure_session.session_key

            try:
                if request.user.is_authenticated():
                    user = request.user
                else:
                    user_session = UserSession.objects.get(secure_session_key=secure_session_key)
                    user_session.save()
                    user = user_session.user
            except UserSession.DoesNotExist:
                if request.user.is_authenticated():
                    user = request.user
                else:
                    username = ''.join(('%x' % random.randint(0, 15)) for i in range(16))
                    user = User.objects.create(
                        username = username,
                        password = '!',
                    )
                user_session = UserSession.objects.create(
                    user = user,
                    secure_session_key = secure_session_key,
                    device_name = ' '.join((request.device.brand_name, request.device.model_name)),
                )
            request.user = user
        else:
            request.secure_session = None

    def process_view(self, request, view_func, view_args, view_kwargs):
        if settings.DEBUG_SECURE:
            return
            
        secure_request = request.is_secure()
        secure_view = isinstance(view_func, SecureView)
        
        # If the non-secure session is marked secure, refuse the request.
        # Likewise, if the secure session isn't marked secure, refuse the
        # request and delete the cookie.
        if request.session.get('is_secure'):
            return HttpResponseForbidden('Invalid session_id', mimetype='text/plain')
        if request.secure_session and not request.secure_session.get('is_secure'):
            resp = HttpResponseForbidden('Invalid secure_session_id', mimetype='text/plain')
            resp.delete_cookie('secure_session_id')
            return resp

        if secure_view and not secure_request:
            uri = request.build_absolute_uri().split(':', 1)
            uri = 'https:' + uri[1]
            return view_func.redirect(uri, request, 'secure')
        if not secure_view and secure_request:
            uri = request.build_absolute_uri().split(':', 1)
            uri = 'http:' + uri[1]
            if uri == 'http://%s/' % request.META.get('HTTP_HOST', ''):
                uri += '?preview=true'
            
            if isinstance(view_func, BaseView):
                return view_func.redirect(uri, request, 'secure')
            else:
                return HttpResponsePermanentRedirect(uri)

    def process_response(self, request, response):
        """
        If request.secure_session was modified, or if the configuration is to
        save the session every time, save the changes and set a session cookie.
        """
        
        if not (request.is_secure() or settings.DEBUG_SECURE):
            return response
            
        try:
            accessed = request.secure_session.accessed
            modified = request.secure_session.modified
        except AttributeError:
            pass
        else:
            if accessed:
                patch_vary_headers(response, ('Cookie',))
            if modified or settings.SESSION_SAVE_EVERY_REQUEST:
                if request.session.get_expire_at_browser_close():
                    max_age = None
                    expires = None
                else:
                    max_age = request.secure_session.get_expiry_age()
                    expires_time = time.time() + max_age
                    expires = cookie_date(expires_time)
                # Save the session data and refresh the client cookie.
                request.secure_session.save()
                response.set_cookie('secure_session_id',
                        request.secure_session.session_key, max_age=max_age,
                        expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                        path=settings.SESSION_COOKIE_PATH,
                        secure=not settings.DEBUG_SECURE)
        return response
