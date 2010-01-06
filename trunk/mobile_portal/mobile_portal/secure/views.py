from oauth import oauth
import urllib, urllib2, urlparse, logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse

from mobile_portal.utils.views import BaseView
from mobile_portal.utils.renderers import mobile_render

from .clients import OAuthHTTPError

logger = logging.getLogger('mobile_portal.oauth')

class SecureView(BaseView):
    pass

class OAuthView(SecureView):
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
             return super(OAuthView, cls).__new__(cls, request, opener, *args, **kwargs)
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
            'breadcrumbs': cls.breadcrumb.render(cls, request, {}, None, *args, **kwargs),
            'error':error,
            'oauth_problem': oauth_problem,
            'token_type': token_type,
            'service_name': cls.service_name,
        }
        return mobile_render(request, context, 'secure/oauth_error')
        