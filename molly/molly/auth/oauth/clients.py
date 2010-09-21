import urllib2

from oauth import oauth

from django.core.exceptions import PermissionDenied

class OAuthHTTPError(urllib2.HTTPError, PermissionDenied):
    def __init__(self, e):
        self.exception = e
    
    def __getattr__(self, key):
        return getattr(self.__dict__['exception'], key)
    def __setattr__(self, key, value):
        if key == 'exception':
            super(OAuthHTTPError, self).__setattr__(key, value)
        else:
            setattr(self.__dict__['exception'], key, value)

class OAuthOpener(object):
    def __init__(self, opener):
        self.__dict__['_opener'] = opener
    
    # Pass everything through to the inner opener
    def __getattr__(self, name):
        return getattr(self._opener, name)
    def __setattr__(self, name, value):
        return setattr(self._opener, name, value)
    def __delattr__(self, name):
        return delattr(self._opener, name)
        
    def open(self, *args, **kwargs):
        try:
            return self.__dict__['_opener'].open(*args, **kwargs)
        except urllib2.HTTPError, e:
            if e.code in (401, 403):
                raise OAuthHTTPError(e)
            else:
                raise
    

class OAuthHandler(urllib2.BaseHandler):
    def __init__(self, consumer, access_token, signature_method):
        self.consumer, self.access_token = consumer, access_token
        self.signature_method = signature_method
        
    def https_request(self, request):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                                   self.access_token)

        if self.access_token:
            oauth_request.sign_request(self.signature_method,
                                       self.consumer,
                                       self.access_token)
            request.add_header('Authorization',
                               oauth_request.to_header()['Authorization'])
        return request
    http_request = https_request

class OAuthClient(oauth.OAuthClient):

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
        return OAuthOpener(urllib2.build_opener(OAuthHandler(consumer,
                                                             access_token,
                                                             signature_method)))
