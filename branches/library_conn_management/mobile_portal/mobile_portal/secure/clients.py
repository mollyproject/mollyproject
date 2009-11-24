from oauth import oauth
import urllib2

class SimpleOAuthClient(oauth.OAuthClient):

    def __init__(self, request_token_url='', access_token_url='', authorization_url=''):
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url

    def fetch_request_token(self, oauth_request):
        # via headers
        # -> OAuthToken
        request = urllib2.Request(self.request_token_url, headers=oauth_request.to_header())
        response = urllib2.urlopen(request) 
        return oauth.OAuthToken.from_string(response.read())

    def fetch_access_token(self, oauth_request):
        # via headers
        # -> OAuthToken
        request = urllib2.Request(self.access_token_url, headers=oauth_request.to_header())
        response = urllib2.urlopen(request) 
        return oauth.OAuthToken.from_string(response.read())

    def authorize_token(self, oauth_request):
        # via url
        # -> typically just some okay response
        response = urllib2.urlopen(oauth_request.to_url()) 
        return response.read()