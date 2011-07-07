# Molly Settings File
#
# This file contains a sample Molly configuration file. It follows the format
# of a standard Django file: https://docs.djangoproject.com/en/dev/topics/settings/
#
# This is also a Python file, so you can define Python strings in here.
#
# The documentation for this file and the settings within it is at:
# http://docs.mollyproject.org/dev/getting-started/configuring.html
#
# It is recommended you use that as a reference whilst moving through this file.

# This next block of code is preamble that is used later on, you can safely
# skip it:
from oauth.oauth import OAuthSignatureMethod_PLAINTEXT
import os, os.path, imp
from molly.conf.settings import Application, extract_installed_apps, Authentication, ExtraBase, Provider
from molly.utils.media import get_compress_groups

# The following creates two useful variables - a path to where Molly is
# installed, and also to the root of where your site is installed. These can be
# used in place of absolute URLs so you can move your installation around
MOLLY_ROOT = imp.find_module('molly')[1]
PROJECT_ROOT = os.path.normpath(os.path.dirname(__file__))

# The next setting defines whether or not the site is in debug mode. In debug
# mode, more verbose logging is available, as well as more information about
# errors which occur. It is recommended to have this turned on when developing
# the site, but to set it to False when running a live site.
DEBUG = True

# This setting decides whether or not the secure parts of the site should be in
# 'debug' mode - when True, this allows Secure parts of the site to be accessed
# over regular HTTP. It defaults to the same value as DEBUG.
DEBUG_SECURE = DEBUG

# This setting decides whether or not template debugging information is shown
# when a template error occurs. It defaults to the same value as DEBUG.
TEMPLATE_DEBUG = DEBUG

# The next setting defines which users receive e-mail notifications of events on
# the site, such as errors, submitted feedback, etc. Multiple e-mail addresses
# can be added multiple comma-seperated tuples.
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

# This is the name of this site which is used in various templates throughout
# the site
SITE_NAME = 'Mobile Portal'

# This defines the database connections for this project
DATABASES = {
    'default': {
        # The next line defines which database type is used. Molly heavily
        # relies on a spatial database, and recommends Postgres/Postgis for this
        # The default below should be fine and not need to change
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        
        # The name of the database to connect to
        'NAME': 'molly',
        
        # The username to connect as
        'USER': 'molly',
        
        # The password to connect with
        'PASSWORD': 'molly',
        
        # The address of the database server - an empty string = localhost
        'HOST': '',
        
        # The port of the database server - an empty string = the server default
        'PORT': '',
    }
}

# This is the e-mail address which Molly uses to send e-mails from
SERVER_EMAIL = 'molly@example.com'

# This is the hostname for the SMTP server to use to send e-mails through
EMAIL_HOST = 'localhost'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

# This list defines which languages are available for your users to use. At
# present, only English is supported, although you can add custom translation
# packs of your own, or add languages when Molly supports them at a later date
LANGUAGES = (
        ('en', 'English'),
    )

# This refers to Django's 'Site' framework, which Molly does not use. It is
# recommended to leave this at its default setting
SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# This defines the SRID (http://en.wikipedia.org/wiki/SRID) which is used by
# Geodjango to compute distances, project co-ordinates, etc. The default is
# fairly sensible.
SRID = 27700

# Absolute filesystem path to the directory that will hold user-uploaded files.
# This setting is unused in Molly.
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'site_media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
# This setting is unused in Molly.
MEDIA_URL = '/site-media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# This defaults to the 'compiled_media' folder in your project.
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'compiled_media')

# URL prefix for static files - this is the address that Molly expects your
# static files to be served from. Apache should be set up to serve the directory
# specified above at this URL
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
# Defaults to the 'admin' subdirectory of the static URL set above
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

# This specifies the path to where Molly caches files (e.g., generated map
# images, resized images, etc)
CACHE_DIR = os.path.join(PROJECT_ROOT, 'cache')

# This specifies where Molly should cache pre-generated map markers. The
# default is in a subdirectory called 'markers' in the cache directory
MARKER_DIR = os.path.join(CACHE_DIR, 'markers')

# This specifies where your external images should be cached. By default, this
# happens under the CACHE_DIR
#EXTERNAL_IMAGES_DIR = '/var/cache/molly-images'

# Additional locations of static files
# This defaults to your local site media folder with highest priority, then any
# default media that Molly comes with, as well as the markers used for slippy
# maps
STATICFILES_DIRS = (
    ('', os.path.join(PROJECT_ROOT, 'site_media')),
    ('', os.path.join(MOLLY_ROOT, 'media')),
    ('markers', MARKER_DIR),
)

# This defines where files should be found to be compressed - this should be
# the folder all the collected media is stored in
COMPRESS_SOURCE = STATIC_ROOT

# This defines where all the compressed files should be stored. You'll want this
# to be in the same place as above
COMPRESS_ROOT = STATIC_ROOT

# This is the URL where the compressed files are expected to be served from. If
# you're saving them in the same place as your regular media (the recommended)
# default, then they're available in the same place
COMPRESS_URL = STATIC_URL

# This uses a Molly convenience function to find the CSS and JS to be compressed
# and which should be concatenated together
COMPRESS_CSS, COMPRESS_JS = get_compress_groups(STATIC_ROOT)

# This determines how the CSS should be compressed
# CSS filter is custom-written since the provided one mangles it too much
COMPRESS_CSS_FILTERS = ('molly.utils.compress.MollyCSSFilter',)

# This determines how the JavaScript should be compressed
COMPRESS_JS_FILTERS = ('compress.filters.jsmin.JSMinFilter',)

# This settings sets whether or not compression is enabled
# In order to help with debugging, then this is only enabled when debugging is
# off
COMPRESS = not DEBUG

# When set, then a version number is added to compressed files, this means
# changing a file also changes its URL - when combined with far future expires,
# then this solves caching issues
COMPRESS_VERSION = True

# Make this unique, and don't share it with anybody. It's used to salt passwords
SECRET_KEY = ''

# This list is used to specifiy which classes are used to help Django find
# templates to be rendered. In most circumstances, there is no reason to change
# this
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader', # First try the templates in the directories specified by TEMPLATE_DIRS
    'django.template.loaders.app_directories.Loader', # Then try the ones that come with the bundled apps
    'molly.utils.template_loaders.MollyDefaultLoader' # Finally, use Molly's molly_default virtual directory
)

# This defines the places Django looks for templates, in order of priority
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'), # first look in the 'templates' folder in your local site
    os.path.join(MOLLY_ROOT, 'templates'), # secondly, look in Molly's default templates
)

# This list specifies which Django middleware clases are used when processing
# requests and responses. For more information about Django middleware, please
# see https://docs.djangoproject.com/en/dev/topics/http/middleware/
# The defaults are fine for most installs
MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware', # This enables Django's cross-site request forgery protection framework
    'molly.wurfl.middleware.WurflMiddleware', # This enables Molly's device detection capability (required)
    'django.middleware.common.CommonMiddleware', # This incorporates some convenience functions from Django (required)
    'django.contrib.sessions.middleware.SessionMiddleware', # This enables Django's session storage framework (required)
    'django.middleware.locale.LocaleMiddleware', # This enables i18n support in Molly (required)
    'molly.utils.middleware.ErrorHandlingMiddleware', # This enables Molly's error handling and reporting framework
    'django.contrib.auth.middleware.AuthenticationMiddleware', # This allows for users to be logged in in Django (required)
    'molly.auth.middleware.SecureSessionMiddleware', # This adds the capability to have secure sessions (sessions which are HTTPS only)
    'molly.apps.stats.middleware.StatisticsMiddleware', # This enables Molly's built in hit logging
    'molly.url_shortener.middleware.URLShortenerMiddleware', # This enables Molly's URL shortening functionality
)

# This list specifies "context processors" which add things to the context which
# are then available in the templates. The defaults are fine for most installs.
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth', # This adds information about the currently logged in user to the context
    'django.core.context_processors.debug', # This allows templates to check whether or not they are in debug mode
    'django.core.context_processors.request', # This adds the current request to the template context
    'molly.utils.context_processors.ssl_media', # This adds STATIC_URL to the template context, which is the base URL to be used for rendering
                                                # when the request is over HTTPS, then STATIC_URL is also changed to be HTTPS if it's a full URI
    'molly.wurfl.context_processors.wurfl_device', # This adds information about the current device to the context
    'molly.wurfl.context_processors.device_specific_media', # This adds information to the context about the capability group this device has been put in
                                                            # for more information about capability groups, see: http://docs.mollyproject.org/dev/topics/supported_devices.html
    'molly.geolocation.context_processors.geolocation', # This adds the current known location of the user to the context
    'molly.utils.context_processors.full_path', # This allows for templates to know the full path to the currently rendered page
    'molly.utils.context_processors.google_analytics', # This adds settings related to Google Analytics to the template contect
    'molly.utils.context_processors.site_name', # This adds the globally configured site name to the template context
    'molly.utils.context_processors.languages', # This adds information about the current and available languages to the context
    'django.core.context_processors.csrf', # This adds a CSRF token to the context which is used for form rendering
)

# This specifies that Django should use Molly's automatically generated Urlconf
# If you're using any non-Molly apps with Molly, you will need to create a
# custom Urlconf
ROOT_URLCONF = 'molly.urls'

# This defines the view that is rendered when a CSRF validation failure occurs
# The default is to use Molly's default templates. If you want to change this
# view, it is instead recommended that you create a new template
# 'csrf_failure.html' in your templates folder and customise that
CSRF_FAILURE_VIEW = 'molly.utils.views.CSRFFailureView'

# This disables Django's built in logger, as Molly comes with its own logging
# framework which can sometimes conflict with Django's
LOGGING_CONFIG = None

# This is used to store API keys for various external services that Molly uses
API_KEYS = {
    
    # This is used for geocoding and location settings. You can obtain an API
    # key by registering at Cloudmade.com and then going to your user profile
    # page: http://cloudmade.com/user/show
    'cloudmade': '',
    
    # This is the web property ID for your Google Analytics account
    'google_analytics': '',
}

# Each entity has a primary identifier which is used to generate the absolute
# URL of the entity page. We can define a list of identifier preferences, so
# that when an entity is imported, these identifier namespaces are looked at in
# order until a value in that namespace is chosen. This is then used as the
# primary identifer. The default is shown in the sample below, and is optional:
#IDENTIFIER_SCHEME_PREFERENCE = ('atco', 'osm', 'naptan', 'postcode', 'bbc-tpeg')

# This is where you define which applications are used in your Molly install
# The order in this file defines the order in which applications appear on the
# home screen
APPLICATIONS = [
    
    # Application definitions look a little bit like this:
    #
    #Application('mysite.myapp', 'myapp', 'My App',
    #    enable_foo = False,
    #    enable_bar = True,
    #),
    #
    # The first argument is the Python package which provides this app, the
    # second is the "local name", which is used as a namespace for URL resolving
    # and as the first part of the URL for all pages in this app. The final
    # part is the application name, as rendered on the home screen. Any options
    # are then listed below as keyword arguments. For more information on the
    # applications framework, as well as all supported references, please see
    # http://docs.mollyproject.org/dev/getting-started/configuring.html#applications
    
    # The home screen - this app must be loaded
    Application('molly.apps.home', 'home', 'Home',
        # This setting is valid on every app, and is used to determine whether
        # or not this app should be included in the list of apps on the home
        # page. It defaults to True, but you can suppress an app from being
        # displayed in the icon grid by setting it to be False
        display_to_user = False,
    ),

    # The desktop page - users with desktop browsers are redirected here to
    # see more information about the app
    Application('molly.apps.desktop', 'desktop', 'Desktop',
        display_to_user = False,
        
        # A stream of tweets can be shown on the desktop page. If this is set,
        # then this feed is fetched and shown. To disable this functionality,
        # just comment out the next line.
        twitter_username = 'mollyproject',
        
        # When this is set, any tweets which contain this URL are filtered out
        # of being displayed - the aim of this is if blog entries are fed into
        # your tweets, then you don't get duplication between showing your blog
        # feed and your feed of tweets
        twitter_ignore_urls = 'http://blog.mollyproject.org',
        
        # If set, then an RSS feed is fetched and rendered on the front page
        blog_rss_url = 'http://blog.mollyproject.org/rss',
    ),

    # A contact search app
    Application('molly.apps.contact', 'contact', 'Contact search',
        
        # Molly ships with an LDAP provider out of the box, however you can
        # write your own provider to do contact search if you desire by changing
        # the package name (first argument) in the line below
        provider = Provider('molly.apps.contact.providers.LDAPContactProvider',
                        # The URL setting defines the URL of the LDAP server to connect to
                        url='ldap://ldap.mit.edu:389',
                        
                        # The base_dn setting specifies the DN to use when querying
                        # the LDAP server
                        base_dn='dc=mit,dc=edu'
                        
                        # This next option allows you to add a prefix to phone
                        # numbers that makes them externally diallable, e.g.,
                        # if your LDAP server stores extension numbers only
                        # The prefix should be international format
                        #phone_prefix='+44123456',
                        
                        # The next option gives you more power than this, by
                        # allowing you to specify a function which filters all
                        # phone numbers and returns a complete string.
                        #phone_formatter = my_custom_function,
            ),
    ),

    # Places is used to store a location database and can be used find places
    # This is required by the transport and library apps
    Application('molly.apps.places', 'places', 'Places',
        
        # This app accepts a list of providers which provide place information
        providers = [
            
            # The NaPTAN is the database of 'Public Transport Access Nodes',
            # that is, places on the public transport network, e.g., train
            # stations, bus stops, etc...
            Provider('molly.apps.places.providers.NaptanMapsProvider',                
                # This specifies which areas of the NaPTAN are to be imported.
                # The full list of codes is available at http://www.dft.gov.uk/naptan/smsPrefixes.htm
                # and the 'ATCO' column is the relevant code here. Also available
                # are areas "920", "930" and "940" which refer to airports,
                # ferry terminals and metro stations respectively. Area '910'
                # represents rail stations and are always imported.
                areas=('340','940'),
            ),
            
            # The postcode importer uses the CodePoint Open database to import
            # postcode areas.
            Provider('molly.apps.places.providers.PostcodesMapsProvider',
                
                # This is the path to where the CodePoint Open file lives on
                # disk. If this file doesn't exist, it is created by downloading
                # from http://www.freepostcodes.org.uk/
                codepoint_path = CACHE_DIR + '/codepo_gb.zip',
                
                # This option specifies which postcode areas are to be imported
                # A postcode area is the first alphabetical component of a
                # postcode, e.g., OX for 'OX2 6NN', YO for 'YO10 5DD'. A full
                # list of postcode areas is available at
                # http://en.wikipedia.org/wiki/List_of_postcode_areas_in_the_United_Kingdom
                # Disabling this setting will import the entire country, but
                # this is not recommended due to the size of the dataset!
                import_areas = ('OX',),
            ),
            
            # This next provider provides real time bus information if you are
            # in an area where ACIS Live provides the infrastructure for real
            # time passenger information. It is recommended that you speak to
            # your local public transport executive/council before enabling this
            # service.
            #
            #'molly.apps.places.providers.ACISLiveMapsProvider',
            
            # The next provider is related to the previous and can extract route
            # details from an ACIS Live instance to provide information about
            # all the bus stops on a particular route. As with the previous one,
            # it is recommended you talk to your council before enabling this
            # service
            #
            #Provider('molly.apps.places.providers.ACISLiveRouteProvider',
            #    # This next option specifies the URLs for the ACIS Live instances
            #    # which are to be scraped to obtain the route data.
            #    urls = ('http://www.oxontime.com',),
            #),
            
            # The next provider uses the Trackernet API to provide real-time
            # information on Tube departures at London Underground stations
            'molly.apps.places.providers.TubeRealtimeProvider',
            
            # This provider uses OpenStreetMap data to provide points of
            # interest for the places app.
            Provider('molly.apps.places.providers.OSMMapsProvider',
                     
                     # The following specify a bounding box for the OSM data
                     # to be imported. It uses decimal latitude and longitude
                     # degrees
                     lat_north=52.1, # The northern limit on the bounding box
                     lat_south=51.5, # The southern limit on the bounding box
                     lon_west=-1.6, # The western limit on the bounding box
                     lon_east=-1.0 # The eastern limit on the bounding box
                     
                     # The following URL specifies a link to a bzip2'd OSM dump
                     # file to use. It defaults to the English file. Using the
                     # most specific file for your needs will improve running
                     # time. http://download.geofabrik.de/osm/ contains country
                     # and region specific data dumps
                     #url='http://download.geofabrik.de/osm/europe/great_britain/england.osm.bz2',
                     
                     # The following setting specifies that instead of using the
                     # default mapping from OSM tags to entity types inside of
                     # Molly, then a different mapping should be used. The second
                     # file contains the specifications for the Molly entity types
                     # which the OSM importer uses.
                     # For more information see http://docs.mollyproject.org/dev/ref/apps/places.html#molly-apps-places-providers-osmmapsprovider
                     #
                     #osm_tags_data_file=os.path.join(PROJECT_ROOT, 'data', 'osm_tags.yaml'),
                     #entity_type_data_file=os.path.join(PROJECT_ROOT, 'data', 'osm_entity_types.yaml')
            ),
            
            # The following provider provides real-time rail departure
            # information from the National Rail Enquiries "Darwin" Live
            # Departure Boards API. You will need an access token to use this
            # service, which can be obtained by contacting National Rail:
            # http://realtime.nationalrail.co.uk/ldbws/
            
            #Provider('molly.apps.places.providers.LiveDepartureBoardPlacesProvider',
            #    token = ''
            #),
            
            # The following provider uses the BBC TPEG feeds to import travel
            # alerts. Please note that the BBC appear to have discontinued these
            # feeds, so this provider is only included for legacy purposes.
            
            #Provider('molly.apps.places.providers.BBCTPEGPlacesProvider',
            #    # This URL is the URL to the TPEG feed to be imported
            #    url='http://www.bbc.co.uk/travelnews/tpeg/en/local/rtm/oxford_tpeg.xml',
            #),
            
            # The following provider takes timetable and route dumps in ATCO-CIF
            # format and imports those into Molly, allowing for scheduled bus
            # departures to be shown alongside the bus stop
            
            #Provider('molly.apps.places.providers.AtcoCifTimetableProvider',
            #    url = 'http://store.datagm.org.uk/sets/TfGM/GMPTE_CIF.zip'
            #),
            
            # The following provider takes timetable and route dumps from the
            # multiple timetable sources and shows them on the entity page
            
            Provider('molly.apps.places.providers.TimetableAnnotationProvider'),
        ],
        
        # This setting can be used to associate entities with each other. At
        # present this simply means a list of associated entries, with any
        # real-time information, is shown below the original entity on the
        # entity detail page.
        #
        # The format is a list of tuples, where the format is:
        # (identifier_scheme, identifier_value, entity_groups), and
        # entity_groups is then a list of tuples of entity group names and then
        # a list of entities in that group (tuples of identifier scheme and value).
        # The entity scheme and values can be found by looking at the URL for
        # the entity, e.g., http://example.com/places/atco:9100OXFD/ has a
        # scheme of 'atco' and a value of '9100OXFD'
        #
        # Below is an example definition for associating bus stops near Oxford
        # rail station (those in the Forecourt, and then those a little bit
        # further away, on Frideswide Square) with the station.
        #
        #associations = [
        #    ('atco', '9100OXFD', [
        #        ('Station Forecourt', [
        #            ('atco', '340000006R1'),
        #            ('atco', '340000006R2'),
        #            ('atco', '340000006R3'),
        #            ('atco', '340000006R4'),
        #            ('atco', '340000006R5'),
        #            ('atco', '340000006R6'),
        #        ]),
        #        ('Frideswide Square', [
        #            ('atco', '340002070R7'),
        #            ('atco', '340002070R8'),
        #            ('atco', '340002070R9'),
        #            ('atco', '340002070R10'),
        #        ]),
        #    ]),
        #]

    ),

    # The following app enables library searching
    Application('molly.apps.library', 'library', 'Library search',
        
        # If your libraries exist as entities in the places app, and they have
        # identifiers which correspond to the location codes returned by your
        # library catalogue, then you can set the namespace for this identifier
        # here and it is used for location sensitive library searching
        #library_identifier = 'olis',
        
        # The provider which provides the search backend. At present, only
        # Z39.50 is supported
        provider = Provider('molly.apps.library.providers.Z3950',
                            
                            # The hostname of the Z39.50 endpoint to connect to
                            host = 'library.example.ac.uk',
                            
                            # The database name to use
                            database = 'Default',
                            
                            # Optionals - specifies the port to connect to on
                            # the server
                            #port=210,
                            
                            # Optional - defaults to USMARC, the syntac which
                            # records are returned in (USMARC and XML supported)
                            syntax='USMARC',
                            
                            # Optional - the charset to use when communicating
                            # with the server - defaults to UTF-8
                            #charset = 'ascii',
                            
                            # Optional - the 'use attribute' to use when looking
                            # up by control number, defaults to 12
                            #control_number_key='1032'
                            ),
    ),

    # Gathers together places and data relating to transport and shows them all
    # in one place
    Application('molly.apps.transport', 'transport', 'Transport',
        
        # If set, then specifies the ID of the rail station to show on the
        # transport page. You can specify the CRS code by using crs:CODE, where
        # code is a station from this list: http://www.nationalrail.co.uk/stations/codes/
        #train_station = 'crs:OXF',
        
        # If set to True, then instead of the train station specified above,
        # then the closest train station to the user is shown. The train station
        # specified above is then only used as a fallback
        train_station_nearest = False,
        
        # This specifies which other nearby entity types are to be shown on
        # the transport page. It is a dictionary where the key represents the
        # ID of the <div> which contains it, and the value is a tuple of type
        # slug (i.e., from http://example.com/places/category/TYPE-SLUG/) and
        # the number to show by default
        nearby = {
            
            # This shows the 5 nearest bus stops
            'bus': ('bus-stop', 5),
            
            # This shows the 3 nearest Supertram stops
            #'supertram': ('supertram-stop', 3),
        },
        
        # When set, then this shows the park and rides specified below on the
        # transport page. These are in the form SCHEME:VALUE
        
        #park_and_rides = [
        #    'osm:W4333225',
        #    'osm:W4329908',
        #    'osm:W34425625',
        #    'osm:W24719725',
        #    'osm:W2809915'],
        
        # When set to True, this shows current travel alerts on the transport
        # page
        travel_alerts = False,
        
        # The next setting refers to a provider which provides "line status"
        # about a public transport system (e.g., Tube, tram, etc). Molly only
        # comes with one provider for this, a London Underground line status
        # provider, uncomment the line below to enable this
        #transit_status_provider = 'molly.apps.transport.providers.TubeStatusProvider',
    ),
    
    # The following app allows for podcasts to be shown
    Application('molly.apps.podcasts', 'podcasts', 'Podcasts',
        # The following setting lists all the sources for podcasts for this app
        # Any provider can appear multiple times, for example to import multiple
        # OPML feeds
        providers = [
            
            # The following provider enables import from an OPML feed
            Provider('molly.apps.podcasts.providers.OPMLPodcastsProvider',
                
                # This specifies the URL of the feed to be imported
                url = 'http://www.bbc.co.uk/radio/opml/bbc_podcast_opml_v2.xml',
                
                # The following is a regex where the matching group is extracted
                # to be used as the slug in the URLs generated inside Molly
                rss_re = r'http://downloads.bbc.co.uk/podcasts/(.+)/rss.xml'
            ),
            
            # The following provider enables import from an PodcastProducer feed
            Provider('molly.apps.podcasts.providers.PodcastProducerPodcastsProvider',
                
                # This specifies the URL of the feed to be imported
                url = 'http://www.example.com/feed.pp',
                
            ),
            
            # The following provider imports single RSS feeds
            Provider('molly.apps.podcasts.providers.RSSPodcastsProvider',
                podcasts = [
                    # The feeds to import are specified here in the form:
                    #('slug', 'http://example.com/feed.rss'),
                ],
                
                # The setting below determines the type of this set of RSS feeds
                # either 'audio' or 'video'. If omitted, it defaults to undefined.
                #medium = 'audio'
            ),
        ]
    ),

    # The following app enables webcams in Molly, comment it out or delete it
    # to disable it. There are no additional settings, as webcams are added
    # using the web interface at http://example.com/adm/
    Application('molly.apps.webcams', 'webcams', 'Webcams'),

    # The following app displays the current weather on the front page and a
    # 3-day forecast on a specific weather page
    Application('molly.apps.weather', 'weather', 'Weather',
        
        # This specifies which weather is to be rendered. It is specified in the
        # form PROVIDER/ID - for the default BBC provider, it should be bbc/ID,
        # where ID is the location specific ID in the URL for that area. e.g.,
        # http://news.bbc.co.uk/weather/forecast/9 is the page for Manchester,
        # and the number at the end (9) indicates the location ID
        location_id = 'bbc/9',
        
        # This specifies where Molly gets its weather data from. At present,
        # only a BBC Weather RSS feed parser exists
        provider = Provider('molly.apps.weather.providers.BBCWeatherProvider',
            # This is the BBC location ID, discovered in the same way as
            # described above
            location_id = 9,
        ),
    ),

    # This app allows you to display service status information about your
    # systems
    Application('molly.apps.service_status', 'service-status', 'Service status',
        
        # Below, we specify the sources of service status information. Providers
        # can be repeated in order to specify multiple sources in the same format
        providers = [
            
            # The only provider that ships with Molly is one which parses RSS
            # service status feeds (http://web.resource.org/rss/1.0/modules/servicestatus/)
            Provider('molly.apps.service_status.providers.RSSModuleServiceStatusProvider',
                
                # This is the name for the group of services represented in this RSS feed
                name='IT Services',
                
                # This is a slug for this feed
                slug='itserv',
                
                # This is the source URL of the feed
                url='http://example.com/servicestatus.rss')
        ],
    ),

    # The following app enables site-wide search in Molly. It can be disabled,
    # but this does not remove UI elements that refer to it, so it is recommended
    # this is kept enabled for now
    Application('molly.apps.search', 'search', 'Search',
        
        # Below you can provide a list of sources of search results, which will
        # be tried in order
        providers = [
            
            # This provider attempts to do internal search, e.g., by matching
            # names of podcasts, places, etc. This also provides functionality
            # like bus stop code lookup and bus route lookup. It has no options.
            Provider('molly.apps.search.providers.ApplicationSearchProvider'),
            
            # This provider allows the site to use an institutional Google
            # Search Appliance, which provides full-text searching over the
            # entire site
            #Provider('molly.apps.search.providers.GSASearchProvider',
            #    # This is the URL of the GSA search endpoint
            #    search_url = 'http://gsa.example.ac.uk/search',
            #
            #    # This is the domain to search in - it should be the domain of
            #    # your Molly deployment
            #    domain = 'example.ac.uk',
            #
            #    # This is a list of extra parameters which are put in the
            #    # request sent to the Google Search Applicance - optional
            #    #params = {
            #    #    'client': 'molly',
            #    #    'frontend': 'mobile',
            #    #},
            #
            #    # This is a regex which cleans up page titles to show them in
            #    # their normal form - optional
            #    title_clean_re = r'molly \| (.*)',
            #),
        ],
        
        # A query expansion file can be specified (using Google Search Appliance
        # syntax) which is applied to the search terms before they are executed
        #query_expansion_file = os.path.join(project_root, 'data', 'query_expansion.txt'),
        
        display_to_user = False,
    ),

    # This is a utility app for Molly to support feed importing
    Application('molly.apps.feeds', 'feeds', 'Feeds',
        # The providers specify the kind of feeds this feed importer supports
        providers = [
            # Only RSS is supported right now - this has no options
            Provider('molly.apps.feeds.providers.RSSFeedsProvider'),
        ],
        display_to_user = False,
    ),

    # This enables the 'News' app in Molly. This has no options here, and new
    # news feeds are added to the backend at http://example.com/adm/
    Application('molly.apps.feeds.news', 'news', 'News'),
    
    # This enables the 'Events' app in Molly. This has no options here, and new
    # event feeds are added to the backend at http://example.com/adm/
    Application('molly.apps.feeds.events', 'events', 'Events'),

    # This is a utility app to support rendering maps
    Application('molly.maps', 'maps', 'Maps',
        display_to_user = False,
    ),

    # This app is a required app that allows users set their locations within
    # Molly
    Application('molly.geolocation', 'geolocation', 'Geolocation',
        
        # If you want to limit the ability of your users to set their location
        # to only the area your app covers, you can specify this below. The
        # first two parts are the latitude and longitude of the centre of your
        # area, and the last is the distance in metres which the area should be
        # limited to - this does not apply to users who set their location
        # automatically using the JavaScript Geolocation APIs
        #prefer_results_near = (-1.25821, 51.75216, 5000),
        
        # The following providers define how Molly attempts to find a user's
        # location when it's set in a freeform text box
        providers = [
            
            # This provider allows people to set their location to be the
            # same as place Molly knows about - this can be a postcode, for
            # example
            Provider('molly.geolocation.providers.PlacesGeolocationProvider'
                     
                     # The following setting limits this to certain identifier
                     # namespaces, rather than all namespaces and entity names
                     #search_identifiers=('postcode',),
            ),
            
            # This uses Cloudmade's freeform geocoding API to try and identify
            # user input
            Provider('molly.geolocation.providers.CloudmadeGeolocationProvider',
                
                # When the next option is set, then it is appended to requests
                # sent to Cloudmade to try and reduce the results Cloudmade
                # could send. e.g., if search_locality is Oxford, and a user
                # attempts to set their location to be "High Street", then the
                # request that gets send to Cloudmade is "High Street, Oxford"
                #search_locality = 'Oxford',
            ),
        ],
        
        # The next setting controls how often users' phones are asked for a new
        # location, in seconds
        #location_request_period = 900,
        
        display_to_user = False,
    ),
    
    # This enables Molly's feedback functionality (an e-mail feedback form)
    # This has no options
    Application('molly.apps.feedback', 'feedback', 'Feedback',
        display_to_user = False,
    ),

    # This is a utility app that allows for images to be resized to an appropriate
    # size for the phone. It has no configuration.
    Application('molly.external_media', 'external-media', 'External Media',
        display_to_user = False,
    ),

    # This app represents Molly's device detection facility
    Application('molly.wurfl', 'device-detection', 'Device detection',
        display_to_user = False,
        
        # When set to True, this exposes a single page at http://example.com/device-detection/
        # which allows users to see what phone the site thinks they are using
        # This is useful for debugging
        expose_view = True,
    ),

    # This app collects hit records of visitors to the site and logs them to the
    # database. It also renders a number of simple reports based on these stats
    # at the http://example.com/stats/ page. It has no configuration, but depends
    # on and is depended on by the molly.apps.stats middleware defined above.
    Application('molly.apps.stats', 'stats', 'Statistics', display_to_user = False),

    # This app implements the URL shortening functionality inside Molly
    Application('molly.url_shortener', 'url-shortener', 'URL Shortener',
        display_to_user = False,
    ),

    # This app represents Molly's core utilities. It has no configuration.
    Application('molly.utils', 'utils', 'Molly utility services',
        display_to_user = False,
    ),

    # This app represents a feature voting system, where users can suggest
    # features and then vote on ones they would like to see implemented. It has
    # no configuration and is managed from the admin interface.
    Application('molly.apps.feature_vote', 'feature-suggestions', 'Feature suggestions',
        display_to_user = False,
    ),

    # This supports authentication within Molly
    Application('molly.auth', 'auth', 'Authentication',
        display_to_user = False,
        
        # This specifies that this page can only be seen over a HTTPS connection
        # when in non-debug mode
        secure = True,
        
        # The following setting determines which user identifiers are used when
        # considering if two different user sessions are indeed the same (single
        # sign on for linked services)
        unify_identifiers = ('weblearn:id',),
    ),

    # This enables mobile integration with the Sakai VLE
    #Application('molly.apps.sakai', 'sakai', 'Sakai',
    #    
    #    # This is the hostname of the Sakai endpoint to connect to
    #    host = 'https://sakai.example.ac.uk/',
    #    
    #    # This is the name which shows up in the manage authentication screen
    #    service_name = 'Sakai',
    #    
    #    # This limits access to this service to HTTPS only
    #    secure = True,
    #    
    #    # The following list defines which Sakai tools are exposed to users, and
    #    # the publicly facing name which is used
    #    tools = [
    #        ('signup', 'Sign-ups'),
    #        ('poll', 'Polls'),
    #        ('direct', 'User information'),
    #        ('sites', 'Sites'),
    #        ('evaluation', 'Surveys'),
    #    ],
    #    
    #    # The following enables OAuth integration between Sakai and Molly. Any
    #    # custom apps wishing to use OAuth can follow this template
    #    extra_bases = (
    #        ExtraBase('molly.auth.oauth.views.OAuthView',
    #            # This should be your OAuth secret token
    #            secret = '',
    #            
    #            # This is how the OAuth request is signed
    #            signature_method = OAuthSignatureMethod_PLAINTEXT(),
    #            
    #            # This is the base URL to the OAuth endpoint
    #            base_url = 'https://weblearn.ox.ac.uk/oauth-tool/',
    #            
    #            # The following 3 settings define what should be appended to the
    #            # URL above to get the request token, access token and authorise
    #            # endpoints, respectively
    #            request_token_url = 'request_token',
    #            access_token_url = 'access_token',
    #            authorize_url = 'authorize',
    #        ),
    #    ),
    #    
    #    # When set to True, this means that users will be logged out after a
    #    # period of inactivity. When False, they will stay logged in until they
    #    # manually log out
    #    enforce_timeouts = False,
    #    
    #    # The following defines the mapping between Sakai user identifiers and
    #    # Molly user identifiers
    #    identifiers = (
    #        ('oxford:sso', ('props', 'aid',)),
    #        ('weblearn:id', ('id',)),
    #        ('oxford:oss', ('props', 'oakOSSID',)),
    #        ('oxford:ldap', ('props', 'udp.dn',)),
    #        ('weblearn:email', ('email',)),
    #    ),
    #),
    
    # This app allows for users to favourite pages which can then be jumped to
    # immediately from the front page, or rendered on the nearby page. It has no
    # configuration.
    Application('molly.favourites', 'favourites', 'Favourite pages',
        display_to_user = False,
    ),

]

# This is where any non-Molly apps are added to the configuration
INSTALLED_APPS = extract_installed_apps(APPLICATIONS) + (
    'django.contrib.auth', # Django's user authentication system
    'django.contrib.admin', # Django's admin backend
    'django.contrib.contenttypes', # Django's Content Types API - this is a prerequisite for the admin interface
    'django.contrib.sessions', # Django's sessions API - this is required
    'django.contrib.sites', # Django's sites API, this is a prerequisite for the comments API
    'django.contrib.gis', # Geodjango - this is required
    'django.contrib.comments', # Django's comments API - used in the feature vote app
    'molly.batch_processing', # This is a part of Molly that handles the batch jobs
    'django.contrib.staticfiles', # Staticfiles handles media for Molly
    'compress', # Compress is an external library that minifies JS and CSS
    'south', # South handles changes to database schema
)
