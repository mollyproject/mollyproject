import os.path

from oauth.oauth import OAuthSignatureMethod_PLAINTEXT

from molly.conf.settings import Application, extract_installed_apps, Authentication, ExtraBase, SimpleProvider, Batch

from molly.conf.default_settings import *

from mobile_oxford.secret_store import secrets as SECRETS

SECRET_KEY = SECRETS.secret_key

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), '..', '..', 'templates'),
)


APPLICATIONS = [
    Application('molly.apps.contact', 'contact',
        provider = 'molly.contrib.oxford.providers.ScrapingContactProvider',
#        provider = 'molly.contrib.mit.providers.LDAPContactProvider',
    ),

    Application('molly.apps.weather', 'weather',
        location_id = 'bbc/25',
        provider = SimpleProvider('molly.contrib.generic.providers.BBCWeatherProvider',
            location_id = 25,
            batch = Batch('pull_weather', minute=range(5, 65, 15)),
        ),
    ),

    Application('molly.maps', 'maps',
        sources = [
            'molly.contrib.oxford.sources.NaptanSource',
            'molly.contrib.oxford.sources.OxpointsSource',
            'molly.contrib.oxford.sources.OSMSource',
        ],
    ),

    Application('molly.z3950', 'library',
        provider = SimpleProvider(
            verbose_name = 'Oxford Library Information System',
            host = 'library.ox.ac.uk',
            database = 'MAIN*BIBMAST',
        ),
    ),

    Application('molly.apps.service_status', 'service_status',
        providers = [
            'molly.contrib.oxford.providers.OUCSStatusProvider',
            SimpleProvider('molly.contrib.generic.providers.ServiceStatusProvider',
                name='Oxford Library Information Services',
                slug='olis',
                url='http://www.lib.ox.ac.uk/olis/status/olis-opac.rss')
        ],
    ),

    Application('molly.sakai', 'weblearn',
        host = 'https://weblearn.ox.ac.uk/',
        service_name = 'WebLearn',
        secure = True,
        extra_bases = (
            ExtraBase('molly.auth.oauth.views.OAuthView',
                secret = SECRETS.weblearn,
                signature_method = OAuthSignatureMethod_PLAINTEXT(),
                base_url = 'https://weblearn.ox.ac.uk/oauth-tool/',
                request_token_url = 'request_token',
                access_token_url = 'access_token',
                authorize_url = 'authorize',
            ),
        ),
    ),

    Application('molly.podcasts', 'podcasts',
        providers = [
            SimpleProvider(
                opml = 'http://rss.oucs.ox.ac.uk/metafeeds/podcastingnewsfeeds.opml',
            ),
            SimpleProvider(
                name = 'Top Downloads',
                rss = 'http://rss.oucs.ox.ac.uk/oxitems/topdownloads.xml',
            ),
        ],
    ),

    Application('molly.auth', 'auth',
    ),
]

API_KEYS = {
    'cloudmade': SECRETS.cloudmade,
    'google': SECRETS.google,
    'yahoo': SECRETS.yahoo,
    'fireeagle': SECRETS.fireeagle,
}

INSTALLED_APPS += extract_installed_apps(APPLICATIONS)

ROOT_URLCONF = 'molly.contrib.oxford.urls'
SITE_MEDIA_PATH = os.path.join(os.path.dirname(__file__), 'site-media')
