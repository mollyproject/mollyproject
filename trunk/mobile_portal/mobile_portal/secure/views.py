from oauth import oauth
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from mobile_portal.core.handlers import BaseView

from models import RequestToken

class OAuthView(BaseView):
    def __new__(cls, request, *args, **kwargs):
         request.access_token = request.secure_session.get(cls.access_token_name)
         
         request.consumer = oauth.OAuthConsumer(*cls.consumer_secret)
         request.client = cls.client()
         
         if 'oauth_token' in request.GET:
             return cls.access_token(request)

         if not request.access_token:
             return cls.authorize(request)
             
         opener = request.client.get_opener(request.consumer,
                                            request.access_token,
                                            cls.signature_method)
         
         return super(OAuthView, cls).__new__(request, opener, *args, **kwargs)
        
    def authorize(cls, request):
        
        callback_uri = request.build_absolute_uri()
            
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            request.consumer,
            callback=callback_uri,
            http_url = request.client.request_token_url,
        )
        oauth_request.sign_request(cls.signature_method, request.consumer, None)
        
        token = request.client.fetch_request_token(oauth_request)
        
        RequestToken.objects.create(
            oauth_token=token.key,
            oauth_token_secret=token.secret,
            redirect_to=request.path,
        )
        
        oauth_request = oauth.OAuthRequest.from_token_and_callback(
            token=token,
            http_url=request.client.authorization_url,
        )

        
        return HttpResponseRedirect(oauth_request.to_url())
        
    def access_token(cls, request):
        try:
            token = RequestToken.objects.get(oauth_token=request.GET.get('oauth_token'))
        except RequestToken.DoesNotExist:
            return HttpResponse('', status=400)
            
        token = oauth.OAuthToken(token.oauth_token, token.oauth_token_secret)
        
        print {
            'consumer': request.consumer,
            'token':token,
            'verifier':request.GET.get('oauth_verifier'),
            'http_url': request.client.access_token_url,
        }
        
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            request.consumer,
            token=token,
            verifier=request.GET.get('oauth_verifier'),
            http_url = request.client.access_token_url,
        )
        
        oauth_request.sign_request(cls.signature_method, request.consumer, token)
        print oauth_request.to_header()
        
        token = request.client.fetch_access_token(oauth_request)
        
        print "Happy token", token
        request.secure_session[cls.access_token_name] = token
        
        return HttpResponseRedirect(request.path)
        
        
        