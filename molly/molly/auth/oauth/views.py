from __future__ import absolute_import
import urlparse, urllib2

if not hasattr(urlparse, 'parse_qs'):
    import cgi
    urlparse.parse_qs = cgi.parse_qs
    del cgi

from oauth import oauth

from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied

from molly.utils.views import BaseView

from molly.auth.utils import unify_users
from molly.auth.models import ExternalServiceToken
from molly.auth.oauth.clients import OAuthClient, OAuthHTTPError

class OAuthView(BaseView):
    """
    Private 'abstract' view implementing OAuth authentication.

    See the docstring for OAuthView for more details.
    """

    def __new__(cls, request, *args, **kwargs):

        token_type, access_token = ExternalServiceToken.get(request.user, cls.conf.local_name, (None, None))

        cls.add_consumer_to_request(request)

        if 'oauth_token' in request.GET and token_type == 'request':
            return cls.access_token(request, *args, **kwargs)

        cls.add_opener_to_request(request, access_token if token_type == 'access' else None)

        # If we aren't authenticated but the view requires it then try
        # to obtain a valid oauth token immediately.
        if token_type != 'access' and getattr(cls, 'force_auth', False):
            return cls.authorize(request, *args, **kwargs)

        try:
            return super(OAuthView, cls).__new__(cls, request, *args, **kwargs)
        except OAuthHTTPError, e:
            if e.code == 403 and token_type != 'access':
                return cls.authorize(request, *args, **kwargs)
            else:
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

        ExternalServiceToken.set(request.user, cls.conf.local_name, ('request', token))

        oauth_request = oauth.OAuthRequest.from_token_and_callback(
            token=token,
            http_url=request.client.authorization_url,
        )

        if getattr(cls.conf, 'oauth_authorize_interstitial', True) and not request.GET.get('skip_interstitial') == 'true':
            context = {
                'authorize_url': oauth_request.to_url(),
                'service_name': cls.conf.service_name,
                'breadcrumbs': (
                    cls.conf.local_name,
                    (cls.conf.service_name, reverse('%s:index' % cls.conf.local_name)),
                    (cls.conf.service_name, reverse('%s:index' % cls.conf.local_name)),
                    True,
                    'Authorization required',
                ),
            }
            return cls.render(request, context, 'auth/oauth/authorize')
        else:
            return HttpResponseRedirect(oauth_request.to_url())

    def access_token(cls, request, *args, **kwargs):
        token_type, request_token = ExternalServiceToken.get(request.user, cls.conf.local_name, (None, None))
        if token_type != 'request':
            return HttpResponse('', status=400)

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            request.consumer,
            token=request_token,
            verifier=request.GET.get('oauth_verifier'),
            http_url = request.client.access_token_url,
        )

        oauth_request.sign_request(cls.signature_method, request.consumer, request_token)

        try:
            access_token = request.client.fetch_access_token(oauth_request)
        except OAuthHTTPError, e:
            return cls.handle_error(request, e, 'request_token', *args, **kwargs)

        ExternalServiceToken.set(request.user, cls.conf.local_name, ('access', access_token))

        cls.add_opener_to_request(request, access_token)
        cls.add_user_identifiers(request)
        unify_users(request)

        return HttpResponseRedirect(request.path)

    def handle_error(cls, request, exception, token_type='access', *args, **kwargs):
        body = exception.read()
        try:
            d = urlparse.parse_qs(body)
        except ValueError:
            error = 'unexpected_response'
            oauth_problem = None
        else:
            error = 'oauth_problem'
            oauth_problem = d.get('oauth_problem', [None])[0]

        if token_type == 'access':
            ExternalServiceToken.remove(request.user, cls.conf.local_name)

        try:
            breadcrumbs = cls.breadcrumb(request, {'oauth_problem': True}, *args, **kwargs)
        except Exception, e:
            breadcrumbs = (
                cls.conf.local_name,
                (reverse('%s:index' % cls.conf.local_name), cls.conf.title),
                (reverse('%s:index' % cls.conf.local_name), cls.conf.title),
                True,
                'Authentication error',
            )

        context = {
            'breadcrumbs': breadcrumbs,
            'error':error,
            'oauth_problem': oauth_problem,
            'token_type': token_type,
            'service_name': cls.conf.service_name,
        }
        return cls.render(request, context, 'auth/oauth/error')

    def add_consumer_to_request(cls, request):

        request.consumer = oauth.OAuthConsumer(*cls.secret)

        request.client = OAuthClient(
            cls.base_url+cls.request_token_url,
            cls.base_url+cls.access_token_url,
            cls.base_url+cls.authorize_url,
        )

    def add_opener_to_request(cls, request, access_token):
        request.opener = request.client.get_opener(
            request.consumer,
            access_token,
            cls.signature_method)

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

