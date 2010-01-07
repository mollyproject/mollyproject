import time

from django.conf import settings
from django.utils.cache import patch_vary_headers
from django.utils.http import cookie_date
from django.utils.importlib import import_module
from django.http import HttpResponseRedirect

from .views import SecureView

class SecureSessionMiddleware(object):
    def process_request(self, request):
        if request.is_secure() or settings.DEBUG:
            engine = import_module(settings.SESSION_ENGINE)
            secure_session_key = request.COOKIES.get('secure_session_id', None)
            request.secure_session = engine.SessionStore(secure_session_key)
        else:
            request.secure_session = None

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not (request.is_secure() or settings.DEBUG):
            if SecureView in view_func.__mro__:
                uri = request.build_absolute_uri().split(':', 1)
                uri = 'https:' + uri[1]
                return HttpResponseRedirect(
                    uri
                )
                    

    def process_response(self, request, response):
        """
        If request.secure_session was modified, or if the configuration is to
        save the session every time, save the changes and set a session cookie.
        """
        
        if not (request.is_secure() or settings.DEBUG):
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
                        secure=not settings.DEBUG)
        return response