from django.conf import settings
import oauth.oauth as oauth
from mobile_portal.secure.clients import SimpleOAuthClient

class SakaiOAuthClient(SimpleOAuthClient):
    def __init__(self):
        self.host = settings.SAKAI_HOST
        super(SakaiOAuthClient, self).__init__(
            self.host+'oauth-tool/request_token',
            self.host+'oauth-tool/access_token',
            self.host+'oauth-tool/authorize',
        )
