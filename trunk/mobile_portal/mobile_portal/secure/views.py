from oauth import oauth
import urllib, urllib2, urlparse, logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.forms.util import ErrorList

from mobile_portal.utils.views import BaseView
from mobile_portal.utils.renderers import mobile_render
from mobile_portal.utils.breadcrumbs import BreadcrumbFactory, Breadcrumb, static_reverse, lazy_reverse

from .clients import OAuthHTTPError
from .forms import PreferencesForm

logger = logging.getLogger('mobile_portal.oauth')

class SecureView(BaseView):
    """
    An 'abstract' view for all secure pages.
    
    Implements a timeout so that people will need to reauthenticate if a
    secure page hasn't been accessed recently. The SecureMidddleware checks
    for this class in a view's MRO in order to enforce an HTTPS connection.
    """
     
    def __new__(cls, request, *args, **kwargs):
        """
        Enforces timeouts for idle sessions.
        """
        
        # If the SecureMiddleware hasn't redirected requests over !HTTPS
        # something has gone wrong. We ignore this for debugging purposes.
        assert settings.DEBUG or request.is_secure()
        
        last_accessed = request.secure_session.get('last_accessed', datetime.now())
        timeout_period = request.secure_session.get('timeout_period', 15)
        if last_accessed < datetime.now() - timedelta(minutes=timeout_period):
            return TimedOutView(request, cls, *args, **kwargs)
        request.secure_session['last_accessed'] = datetime.now()
        
        return super(SecureView, cls).__new__(cls, request, *args, **kwargs)

class TimedOutView(BaseView):
    """
    Handles the case where a user's secure session has been inactive for too
    long.
    
    This view should not be included in a urlconf as it is referenced only by
    SecureView.
    """

    def initial_context(cls, request, view, *args, **kwargs):
        return {
            'has_pin': 'pin' in request.secure_session,
        }    
    
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, view, *args, **kwargs):
        return Breadcrumb(
            view.app_name,
            None,
            'Session expired',
            static_reverse(request.get_full_path()),
        )
    
    def handle_GET(cls, request, context, view, *args, **kwargs):
        return mobile_render(request, context, 'secure/timed_out')
            
    def handle_POST(cls, request, context, view, *args, **kwargs):
        if 'clear_session' in request.POST:
            for key in request.secure_session.keys():
                del request.secure_session[key]
            return HttpResponseRedirect('.')
        elif 'reauthenticate' in request.POST and context['has_pin']:
            valid_pin = request.POST.get('pin') == request.secure_session['pin']
            if valid_pin:
                # Reauthenticating brings the inactivity measure to zero
                request.secure_session['last_accessed'] = datetime.now()
                return HttpResponseRedirect('.')
            else:
                context['incorrect_pin'] = True
                return mobile_render(request, context, 'secure/timed_out')
        else:
            return HttpResponse('', status=400)
        
class IndexView(SecureView):
    app_name = 'secure'
    
    def initial_context(cls, request):
        return {
            'form': PreferencesForm(request.POST or {
                'timeout_period': request.secure_session.get('timeout_period', 15),
            }),
            'has_pin': 'pin' in request.secure_session,
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'secure',
            None,
            'Authentication preferences',
            lazy_reverse('secure_index'),
        )
        
    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'secure/index')
    
    def handle_POST(cls, request, context):
        form = context['form']
        
        if not form.is_valid():
            return mobile_render(request, context, 'secure/index')
            
        if context['has_pin'] and form.cleaned_data['old_pin'] != request.secure_session['pin']:
            form.errors['old_pin'] = ErrorList(['You supplied an incorrect PIN. Please try again.'])
            return mobile_render(request, context, 'secure/index')

        request.secure_session['timeout_period'] = form.cleaned_data['timeout_period']
        
        if form.cleaned_data['new_pin_a']:
            if form.cleaned_data['new_pin_a'] == form.cleaned_data['new_pin_b']:
                request.secure_session['pin'] = form.cleaned_data['new_pin_a']
            else:
                form.errors['new_pin_b'] = ErrorList(['Your repeated PIN did not match.'])
                return mobile_render(request, context, 'secure/index')
        
        return HttpResponseRedirect('.')
        
# Our intention with OAuthView is that it our timeout code is called before we
# do any OAuth token manipulation. Our intended Method Resolution Order is
# therefore [SecureView, _OAuthView, BaseView], with the latter despatching to
# the handle_METHOD methods. To acheive this we have a _OAuthView that handles
# OAuth tokens without worrying about more general secured page issues.
# Finally we have OAuthView which subclasses SecureView and _OAuthView to
# provide the desired MRO. OAuthView has an empty definition (i.e. 'pass') and
# exists solely to twiddle the MRO.
# See [0] for more information about the Python Method Resolution Order.
# 
# [0] http://www.python.org/download/releases/2.3/mro/

class _OAuthView(BaseView):
    """
    Private 'abstract' view implementing OAuth authentication.
    
    See the docstring for OAuthView for more details.
    """
    
    def __new__(cls, request, *args, **kwargs):
         token_type, request.access_token = request.secure_session.get(cls.access_token_name, (None, None))
         
         request.consumer = oauth.OAuthConsumer(*cls.consumer_secret)
         request.client = cls.client()
         
         if 'oauth_token' in request.GET and token_type == 'request_token':
             return cls.access_token(request, *args, **kwargs)

         if token_type != 'access_token':
             return cls.authorize(request, *args, **kwargs)
             
         opener = request.client.get_opener(request.consumer,
                                            request.access_token,
                                            cls.signature_method)
         
         try:
             return super(_OAuthView, cls).__new__(cls, request, opener, *args, **kwargs)
         except OAuthHTTPError, e:
             return cls.handle_error(request, e.exception, *args, **kwargs)
        
    def authorize(cls, request, *args, **kwargs):
        
        callback_uri = request.build_absolute_uri()
            
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            request.consumer,
            callback=callback_uri,
            http_url = request.client.request_token_url,
        )
        oauth_request.sign_request(cls.signature_method, request.consumer, None)
        
        token = request.client.fetch_request_token(oauth_request)
        
        request.secure_session[cls.access_token_name] = 'request_token', token
        
        oauth_request = oauth.OAuthRequest.from_token_and_callback(
            token=token,
            http_url=request.client.authorization_url,
        )

        
        return HttpResponseRedirect(oauth_request.to_url())
        
    def access_token(cls, request, *args, **kwargs):
        token_type, request_token = request.secure_session.get(cls.access_token_name, (None, None))
        if token_type != 'request_token':
            return HttpResponse('', status=400)
        
        print {
            'consumer': request.consumer,
            'token':request_token,
            'verifier':request.GET.get('oauth_verifier'),
            'http_url': request.client.access_token_url,
        }
        
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            request.consumer,
            token=request_token,
            verifier=request.GET.get('oauth_verifier'),
            http_url = request.client.access_token_url,
        )
        
        oauth_request.sign_request(cls.signature_method, request.consumer, request_token)
        print oauth_request.to_header()
        
        try:
            access_token = request.client.fetch_access_token(oauth_request)
        except urllib2.HTTPError, e:
            return cls.handle_error(request, e, 'request_token', *args, **kwargs)
        
        print "Happy token", access_token
        request.secure_session[cls.access_token_name] = "access_token", access_token
        
        return HttpResponseRedirect(request.path)
        
    def handle_error(cls, request, exception, token_type='access_token', *args, **kwargs):
        body = exception.read()
        try:
            d = urlparse.parse_qs(body)
        except ValueError:
            error = 'unexpected_response'
            oauth_problem = None
        else:
            error = 'oauth_problem'
            oauth_problem = d.get('oauth_problem', [None])[0]

        if token_type == 'access_token':
            request.secure_session[cls.access_token_name] = (None, None)
        
        context = {
            'breadcrumbs': cls.breadcrumb(request, {}, None, *args, **kwargs),
            'error':error,
            'oauth_problem': oauth_problem,
            'token_type': token_type,
            'service_name': cls.service_name,
        }
        return mobile_render(request, context, 'secure/oauth_error')

class OAuthView(SecureView, _OAuthView):
    pass
    
class ClearSessionView(SecureView):
    def initial_context(cls, request):
        return {
            'path': request.REQUEST.get('path'),
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return breadcrumb(
            'secure',
        )
            
    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'secure/clear_session')
    def handle_POST(cls, request, context):
        for key in request.secure_session.keys():
            del request.secure_session[key]
        if context['path']:
            return HttpResponseRedirect(context['path'])
        else:
            return HttpResponseRedirect('.')
