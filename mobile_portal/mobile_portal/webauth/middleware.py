
from models import WebauthUser
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse

"""
This is our authentication middleware.
"""

class BinAuthMiddleware(object):
    def process_request(self, request):
        request.is_authenticated = request.user.is_authenticated()
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        This middleware handles what authenticated and non-authenticated users
        can look at. By default, one needs to be logged in to view anything,
        though this can be changed through the use of allow_unauth
        and require_unauth decorators on view methods.
        """
        
        if not hasattr(view_func, 'allow_unauth') and not request.user.is_authenticated() \
           and not (hasattr(view_func, 'require_unauth') or hasattr(view_func, 'allow_unauth')):
            try:
                return HttpResponseRedirect(view_func.require_auth)
            except AttributeError:
                return HttpResponseRedirect(reverse('auth_login') + "?redirect_url=" + request.path)
        elif hasattr(view_func, 'require_unauth') and request.user.is_authenticated():
            return HttpResponseRedirect(view_func.require_unauth or reverse("home"))
        return None

