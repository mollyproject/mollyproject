from __future__ import absolute_import
import urlparse
import urllib
import urllib2
from datetime import timedelta

if not hasattr(urlparse, 'parse_qs'):
    import cgi
    urlparse.parse_qs = cgi.parse_qs
    del cgi

from oauth import oauth

from django.http import Http404, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied, ImproperlyConfigured

from molly.utils.views import BaseView

from molly.auth import unify_users
from molly.auth.models import ExternalServiceToken
from molly.auth.oauth.clients import OAuthClient, OAuthHTTPError

class OAuthView(BaseView):
    """
    Private 'abstract' view implementing OAuth authentication.

    See the docstring for OAuthView for more details.
    """

    def __call__(self, request, *args, **kwargs):

        token_type, access_token = ExternalServiceToken.get(request.user, self.conf.local_name, (None, None))

        self.add_consumer_to_request(request)

        if 'oauth_token' in request.GET and token_type == 'request':
            return self.access_token(request, *args, **kwargs)

        self.add_opener_to_request(request, access_token if token_type == 'access' else None)

        # If we aren't authenticated but the view requires it then try
        # to obtain a valid oauth token immediately.
        if token_type != 'access' and getattr(self, 'force_auth', False):
            return self.authorize(request, *args, **kwargs)

        try:
            return super(OAuthView, self).__call__(request, *args, **kwargs)
        except OAuthHTTPError, e:
            if e.code in (401, 403) and not (token_type == 'request' and 'oauth_token' in request.GET):
                return self.authorize(request, *args, **kwargs)
            else:
                return self.handle_error(request, e.exception, *args, **kwargs)

    def authorize(self, request, *args, **kwargs):

        scheme, netloc, path, params, query, fragment = urlparse.urlparse(request.build_absolute_uri())
        args = urlparse.parse_qs(query)
        if 'format' in args:
            del args['format']
        query = urllib.urlencode(args)
        callback_uri = urlparse.urlunparse((scheme, netloc, path, params, query, fragment))
        
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            request.consumer,
            callback=callback_uri,
            http_url = request.client.request_token_url,
        )
        
        try:
            oauth_request.sign_request(self.signature_method, request.consumer, None)
        except TypeError, e:
            raise ImproperlyConfigured("No OAuth shared secret has been set for app %r. Check that the server is configured with the right credentials." % self.conf.local_name)

        try:
            token = request.client.fetch_request_token(oauth_request)
        except urllib2.HTTPError, e:
            if e.code == 401:
                raise ImproperlyConfigured("OAuth shared secret not accepted by service %r. Check that the server is configured with the right credentials." % self.conf.service_name)
            else:
                return self.handle_error(request, e)

        ExternalServiceToken.set(request.user, self.conf.local_name, ('request', token), authorized=False)

        oauth_request = oauth.OAuthRequest.from_token_and_callback(
            token=token,
            http_url=request.client.authorization_url,
        )

        if getattr(self.conf, 'oauth_authorize_interstitial', True) and not request.GET.get('skip_interstitial') == 'true':
            index_url = reverse('%s:index' % self.conf.local_name)
            context = {
                'return_url': request.META.get('HTTP_REFERER', index_url),
                'authorize_url': oauth_request.to_url(),
                'service_name': self.conf.service_name,
                'breadcrumbs': (
                    self.conf.local_name,
                    (self.conf.service_name, index_url),
                    (self.conf.service_name, index_url),
                    True,
                    'Authorization required',
                ),
            }
            return self.render(request, context, 'auth/oauth/authorize', expires=timedelta(days=-1))
        else:
            return self.redirect(oauth_request.to_url(), request, 'seeother')

    def access_token(self, request, *args, **kwargs):
        token_type, request_token = ExternalServiceToken.get(request.user, self.conf.local_name, (None, None))
        if token_type != 'request':
            return HttpResponseBadRequest()
        if request_token.key != request.GET.get('oauth_token'):
            return HttpResponseBadRequest()

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            request.consumer,
            token=request_token,
            verifier=request.GET.get('oauth_verifier'),
            http_url = request.client.access_token_url,
        )

        oauth_request.sign_request(self.signature_method, request.consumer, request_token)

        try:
            access_token = request.client.fetch_access_token(oauth_request)
        except urllib2.HTTPError, e:
            return self.handle_error(request, e, 'request_token', *args, **kwargs)

        ExternalServiceToken.set(request.user, self.conf.local_name, ('access', access_token), authorized=True)

        self.add_opener_to_request(request, access_token)
        self.add_user_identifiers(request)
        unify_users(request)

        return self.redirect(request.path, request)

    def handle_error(self, request, exception, token_type='access', *args, **kwargs):
        body = exception.read()
        try:
            d = urlparse.parse_qs(body)
        except ValueError:
            error = 'unexpected_response'
            oauth_problem = None
        else:
            error = 'oauth_problem'
            oauth_problem = d.get('oauth_problem', [None])[0]

        ExternalServiceToken.remove(request.user, self.conf.local_name)

        try:
            breadcrumbs = self.breadcrumb(request, {'oauth_problem': True}, *args, **kwargs)
        except Exception, e:
            breadcrumbs = (
                self.conf.local_name,
                (reverse('%s:index' % self.conf.local_name), self.conf.title),
                (reverse('%s:index' % self.conf.local_name), self.conf.title),
                True,
                'Authentication error',
            )

        context = {
            'breadcrumbs': breadcrumbs,
            'error':error,
            'oauth_problem': oauth_problem,
            'token_type': token_type,
            'service_name': self.conf.service_name,
        }
        return self.render(request, context, 'auth/oauth/error', expires=timedelta(days=-1))

    def add_consumer_to_request(self, request):

        request.consumer = oauth.OAuthConsumer(*self.secret)

        request.client = OAuthClient(
            self.base_url+self.request_token_url,
            self.base_url+self.access_token_url,
            self.base_url+self.authorize_url,
        )

    def add_opener_to_request(self, request, access_token):
        request.opener = request.client.get_opener(
            request.consumer,
            access_token,
            self.signature_method)

        def urlopen(*args, **kwargs):
            try:
                return request.opener.open(*args, **kwargs)
            except urllib2.HTTPError, e:
                if e.code == 404:
                    raise Http404
                elif e.code == 403 and access_token is not None:
                    raise PermissionDenied
                else:
                    raise
        request.urlopen = urlopen

    def add_user_identifiers(request):
        pass

