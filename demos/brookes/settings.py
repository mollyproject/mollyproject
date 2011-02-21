## Django settings for Mobile Brookes project.

from oauth.oauth import OAuthSignatureMethod_PLAINTEXT
import os.path
from molly.conf.settings import Application, extract_installed_apps, Authentication, ExtraBase, Provider
from secrets import SECRETS

project_root = os.path.normpath(os.path.dirname(__file__))

SITE_NAME = 'Mobile Brookes'
DEBUG = True
DEBUG_SECURE = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
    ('Mobile Oxford','agajwani@brookes.ac.uk'),	
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = SECRETS.database_name             # Or path to database file if using sqlite3.
DATABASE_USER = SECRETS.database_user             # Not used with sqlite3.
DATABASE_PASSWORD = SECRETS.database_password         # Not used with sqlite3.
DATABASE_HOST = SECRETS.database_host             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/site-media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin-media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = SECRETS.secret_key

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'molly.wurfl.middleware.WurflMiddleware',
#    'molly.auth.middleware.SecureSessionMiddleware',
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
#    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
#    'django.contrib.messages.context_processors.messages',
    'molly.wurfl.context_processors.wurfl_device',
    'molly.wurfl.context_processors.device_specific_media',
    'molly.geolocation.context_processors.geolocation',
    'molly.utils.context_processors.full_path',
)


ROOT_URLCONF = 'brookes.urls'

TEMPLATE_DIRS = (
    os.path.join(project_root, 'templates'),
    # This is temporary until we move the templates to their rightful places
    #os.path.join(project_root, '..', '..', 'molly', 'templates'),
)

APPLICATIONS = [
    Application('molly.apps.home', 'home', 'Home',
        display_to_user = False,
    ),

    Application('molly.apps.contact', 'contact', 'Staff search',
        provider = 'brookes.providers.apps.contact.BrookesContactProvider',
    ),

    Application('molly.apps.places', 'places', 'Places',
        providers = [
            Provider('molly.apps.places.providers.NaptanMapsProvider',
                method='ftp',
                username=SECRETS.journeyweb[0],
                password=SECRETS.journeyweb[1],
                areas=('340',),
            ),
            Provider('molly.apps.places.providers.PostcodesMapsProvider',
                codepoint_path = '/var/cache/molly/codepo_gb.zip',
                import_areas = ('OX',),
            ),
            'molly.apps.places.providers.ACISLiveMapsProvider',
            'molly.apps.places.providers.OSMMapsProvider',
        ],
        nearby_entity_types = (
            ('Transport', (
                'bicycle-parking', 'bus-stop', 'car-park', 'park-and-ride',
                'taxi-rank', 'train-station')),
            ('Amenities', (
                'atm', 'bank', 'bench', 'medical', 'post-box', 'post-office',
                'public-library', 'recycling', 'bar', 'food', 'pub')),
            ('Leisure', (
                'cinema', 'theatre', 'museum', 'park', 'swimming-pool',
                'sports-centre', 'punt-hire')),
            ('University', (
                'university-library', 'college-hall', 'faculty-department',
                'building', 'room')),
        ),

    ),

    Application('molly.apps.library', 'library', 'Library search',
        verbose_name = 'Oxford Library Information System',
        host = 'catalogue.brookes.ac.uk',
        database = 'prod_talis',
        port = 2121,
    ),


    Application('molly.apps.podcasts', 'podcasts', 'Brookes Podcasts',
        providers = [
            Provider('molly.apps.podcasts.providers.PodcastProducerPodcastsProvider',
				url = 'http://gwstream.brookes.ac.uk:8171/podcastproducer/catalogs',
            ),
            Provider('molly.apps.podcasts.providers.RSSPodcastsProvider',
                podcasts = [
                    ('top-downloads', 'http://rss.oucs.ox.ac.uk/oxitems/topdownloads.xml'),
                ],
            ),
        ]
    ),



    Application('molly.apps.webcams', 'webcams', 'Webcams',display_to_user = False),

    Application('molly.apps.weather', 'weather', 'Weather',
        location_id = 'bbc/25',
        provider = Provider('molly.apps.weather.providers.BBCWeatherProvider',
            location_id = 25,
        ),
    ),

    Application('molly.apps.service_status', 'service_status', 'Service status',
        providers = [
            Provider('molly.apps.service_status.providers.RSSModuleServiceStatusProvider',
                name='Oxford Library Information Services',
                slug='olis',
                url='http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/front_page/rss.xml')
        ],
    ),

    Application('molly.apps.search', 'search', 'Search',
        providers = [
            Provider('molly.apps.search.providers.ApplicationSearchProvider'),
            Provider('molly.apps.search.providers.GSASearchProvider',
                search_url = 'http://googlesearch.oucs.ox.ac.uk/search',
                domain = 'm.ox.ac.uk',
                params = {
                    'client': 'oxford',
                },
                title_clean_re = r'm\.ox \| (.*)',
            ),
        ],
        display_to_user = False,
    ),

    Application('molly.apps.feeds', 'feeds', 'Feeds',
        providers = [
            Provider('molly.apps.feeds.providers.RSSFeedsProvider'),
        ],
        display_to_user = False,
    ),

    Application('molly.apps.feeds.news', 'news', 'News'),

#    Application('molly.apps.feeds.news', 'freepc', 'PC Availability'),

    Application('molly.maps', 'maps', 'Maps',
        display_to_user = False,
    ),

    Application('molly.geolocation', 'geolocation', 'Geolocation',
        prefer_results_near = (-1.25821, 51.75216, 5000),
        providers = [
            Provider('molly.geolocation.providers.PlacesGeolocationProvider'),
            Provider('molly.geolocation.providers.CloudmadeGeolocationProvider',
                search_locality = 'Oxford',
            ),
        ],
        display_to_user = False,
    ),

    Application('molly.apps.feedback', 'feedback', 'Feedback',
        display_to_user = False,
    ),

    Application('molly.external_media', 'external_media', 'External Media',
        display_to_user = False,
    ),

    Application('molly.wurfl', 'device_detection', 'Device detection',
        display_to_user = False,
        expose_view = True,
    ),

#    Application('molly.apps.url_shortener', 'url_shortener', 'URL Shortener',
#        display_to_user = False,
#    ),

#    Application('molly.auth', 'auth', 'Authentication',
#        display_to_user = False,
#        secure = True,
#    ),

#    Application('molly.apps.feeds.events', 'events', 'Events',
#    ),
]

API_KEYS = {
    'cloudmade': SECRETS.cloudmade,
    'google': SECRETS.google,
    'yahoo': SECRETS.yahoo,
    'fireeagle': SECRETS.fireeagle,
}

SITE_MEDIA_PATH = os.path.join(project_root, 'site-media')

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'molly.batch_processing',
    'django.contrib.gis',
    'molly.utils',
    'staticfiles',
    'compress',
#    'debug_toolbar',
) + extract_installed_apps(APPLICATIONS)

CACHE_DIR = '/var/cache/molly'
SRID = 27700

FIXTURE_DIRS = [
    os.path.join(project_root, 'fixtures'),
]

INTERNAL_IPS = ('127.0.0.1',)  # for the debug_toolbar

EMAIL_HOST = SECRETS.mail_host
EMAIL_PORT = SECRETS.mail_port


STATIC_ROOT = os.path.join(project_root, 'media')
STATIC_URL = '/media/'
COMPRESS_SOURCE = STATIC_ROOT
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_URL = STATIC_URL