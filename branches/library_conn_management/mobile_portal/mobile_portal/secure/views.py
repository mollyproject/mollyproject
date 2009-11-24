from oauth import oauth
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from mobile_portal.core.handlers import BaseView

from models import RequestToken

class OAuthView(BaseView):
    def __call__(self, request, *args, **kwargs):
         request.access_token = request.secure_session.get(type(self).access_token_name)
         
         request.consumer = oauth.OAuthConsumer(*type(self).consumer_secret)
         request.client = type(self).client()
         
         if 'oauth_token' in request.GET:
             request.access_token = self.access_token(request)

         if not request.access_token:
             return self.authorize(request)
         
         return super(SakaiView, self).__call__(request, *args, **kwargs)
        
    def authorize(self, request):
        
        callback_uri = request.build_absolute_uri()
            
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            request.consumer,
            callback=callback_uri,
            http_url = request.client.request_token_url,
        )
        oauth_request.sign_request(type(self).signature_method, request.consumer, None)
        
        token = request.client.fetch_request_token(oauth_request)
        
        RequestToken.objects.create(
            oauth_token=token.key,
            redirect_to=request.path,
        )
        
        oauth_request = oauth.OAuthRequest.from_token_and_callback(
            token=token,
            http_url=request.client.authorization_url,
        )

        
        return HttpResponseRedirect(oauth_request.to_url())
        
    def access_token(self, request):
        try:
            token = RequestToken.objects.get(oauth_token=request.GET.get('oauth_token'))
        except RequestToken.DoesNotExist:
            return HttpResponse('', status=400)
            
        token = oauth.OAuthToken(token.oauth_token, token.oauth_token_secret)
        
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            request.consumer,
            token=token,
            verifier=request.GET.get('oauth_verifier'),
            http_url = request.client.access_token_url,
        )
        oauth_request.sign_request(type(self).signature_method, request.consumer, token)
        
        token = request.client.fetch_access_token(oauth_request)
        
        request.secure_session[type(self).access_token_name] = token
        
        
        