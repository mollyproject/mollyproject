from __future__ import absolute_import
import urlparse

from oauth import oauth

from django.http import HttpResponseRedirect

from molly.utils.views import BaseView

from molly.auth.oauth.clients import OAuthClient, OAuthHTTPError

class OAuthView(BaseView):
    """
    Private 'abstract' view implementing OAuth authentication.

    See the docstring for OAuthView for more details.
    """

    def __new__(cls, request, *args, **kwargs):
        if not 'oauth_tokens' in request.secure_session:
            request.secure_session['oauth_tokens'] = {}

        token_type, request.access_token = \
            request.secure_session['oauth_tokens'].get(cls.conf.local_name, (None, None))

        request.consumer = oauth.OAuthConsumer(*cls.secret)
        request.client = OAuthClient(
            cls.base_url+cls.request_token_url,
            cls.base_url+cls.access_token_url,
            cls.base_url+cls.authorize_url,
        )

        if 'oauth_token' in request.GET and token_type == 'request_token':
            return cls.access_token(request, *args, **kwargs)

        if token_type != 'access_token':
            return cls.authorize(request, *args, **kwargs)

        request.opener = request.client.get_opener(
            request.consumer,
            request.access_token,
            cls.signature_method)

        try:
            return super(OAuthView, cls).__new__(cls, request, *args, **kwargs)
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

        request.secure_session['oauth_tokens'][cls.conf.local_name] = 'request_token', token
        request.secure_session.modified = True

        oauth_request = oauth.OAuthRequest.from_token_and_callback(
            token=token,
            http_url=request.client.authorization_url,
        )


        return HttpResponseRedirect(oauth_request.to_url())

    def access_token(cls, request, *args, **kwargs):
        token_type, request_token = request.secure_session['oauth_tokens'].get(cls.conf.local_name, (None, None))
        if token_type != 'request_token':
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

        request.secure_session['oauth_tokens'][cls.conf.local_name] = "access_token", access_token
        request.secure_session.modified = True

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
            'breadcrumbs': cls.breadcrumb(request, {}, *args, **kwargs),
            'error':error,
            'oauth_problem': oauth_problem,
            'token_type': token_type,
            'service_name': cls.conf.service_name,
        }
        return cls.render(request, context, 'auth/oauth/error')

