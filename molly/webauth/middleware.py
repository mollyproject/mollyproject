
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse

"""
This is our authentication middleware.
"""

class WebAuthMiddleware(object):
    def process_request(self, request):
        request.is_authenticated = request.user.is_authenticated()
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        This middleware handles what authenticated and non-authenticated users
        can look at. By default, one needs to be logged in to view anything,
        though this can be changed through the use of allow_unauth
        and require_unauth decorators on view methods.
        """
        
        if hasattr(view_func, 'require_auth') and not request.user.is_authenticated():
            if view_func.require_auth:
                return HttpResponseRedirect(view_func.require_auth)
            else:
                return HttpResponseRedirect(reverse('auth_login') + "?redirect_url=" + request.path)
        elif hasattr(view_func, 'require_unauth') and request.user.is_authenticated():
            return HttpResponseRedirect(view_func.require_unauth or reverse("core_index"))
        return None

