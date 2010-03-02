import os.path

from molly.conf.settings import Application, extract_installed_apps, Secret, Authentication, ExtraBase, SimpleProvider

from molly.conf.default_settings import *

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), '..', '..', 'templates'),
)


APPLICATIONS = [
    Application('molly.apps.contact', 'contact',
        provider = 'molly.contrib.oxford.providers.ScrapingContactProvider',
#        provider = 'molly.contrib.mit.providers.ContactProvider',
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
        host = 'https://staging.weblearn.ox.ac.uk/',
        service_name = 'WebLearn',
        secure = True,
        extra_bases = (
            ExtraBase('molly.auth.OAuth',
                secret = Secret('weblearn'),
                signature_method = 'plaintext',
                base_url = 'https://staging.weblearn.ox.ac.uk/oauth-tool/',
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
]

API_KEYS = {
    'cloudmade': Secret('cloudmade'),
    'google': Secret('google'),
    'yahoo': Secret('yahoo'),
    'fireeagle': Secret('fireeagle'),
}

INSTALLED_APPS += extract_installed_apps(APPLICATIONS)
print INSTALLED_APPS

ROOT_URLCONF = 'molly.contrib.oxford.urls'
