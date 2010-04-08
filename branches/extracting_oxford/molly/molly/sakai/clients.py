from django.conf import settings
import oauth.oauth as oauth
from molly.auth.oauth.clients import OAuthClient as BaseOAuthClient

class SakaiOAuthClient(BaseOAuthClient):
    def __init__(self):
        self.host = settings.SAKAI_HOST
        super(SakaiOAuthClient, self).__init__(
            self.host+'oauth-tool/request_token',
            self.host+'oauth-tool/access_token',
            self.host+'oauth-tool/authorize',
        )
