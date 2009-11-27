from oauth import oauth
import urllib2

class OAuthHandler(urllib2.BaseHandler):
    def __init__(self, consumer, access_token, signature_method):
        self.consumer, self.access_token = consumer, access_token
        self.signature_method = signature_method
        
    def http_request(self, request):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                                   self.access_token)
        oauth_request.sign_request(self.signature_method,
                                   self.consumer,
                                   self.access_token)
        request.add_header('Authorization',
                           oauth_request.to_header()['Authorization'])
        print "Auth header", oauth_request.to_header()['Authorization']
        return request

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
        
    def get_opener(self, consumer, access_token, signature_method):
        return urllib2.build_opener(OAuthHandler(consumer,
                                                 access_token,
                                                 signature_method))
