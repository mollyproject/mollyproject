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
import os
import imp
from molly.conf.settings import Application, extract_installed_apps
from molly.conf.settings import ProviderConf as Provider
from molly.conf.celery_util import prepare_celery
from molly.conf.default_settings import *
from molly.utils.media import get_compress_groups

# Celery configuration
BROKER_URL = "amqp://molly:molly@localhost:5672//"
CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
CELERYD_CONCURRENCY = 1
CELERY_RETRY_DELAY = 3 * 60
CELERY_MAX_RETRIES = 3

# Register Django-Celery and initialise our providers.
prepare_celery()

# The following import and mimetypes.add_types correct the - possibly wrong - mime type of svg files
# in certain versions of Django.
import mimetypes

mimetypes.add_type("image/svg+xml", ".svg", True)
mimetypes.add_type("image/svg+xml", ".svgz", True)

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

# This uses a Molly convenience function to find the CSS and JS to be compressed
# and which should be concatenated together
PIPELINE_CSS, PIPELINE_JS = get_compress_groups(STATIC_ROOT)

# This determines how the CSS should be compressed
# CSS filter is custom-written since the provided one mangles it too much
PIPELINE_CSS_COMPRESSOR = 'molly.utils.compress.MollyCSSFilter'

# This determines how the JavaScript should be compressed
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.jsmin.JSMinCompressor'

# Make this unique, and don't share it with anybody. It's used to salt passwords
SECRET_KEY = ''

# This defines the places Django looks for templates, in order of priority
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'), # first look in the 'templates' folder in your local site
    os.path.join(MOLLY_ROOT, 'templates'), # secondly, look in Molly's default templates
)

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

# When converting distances into human readable units, several schemes are
# available: metric (metres and kilometres), imperial (yards and miles) and
# british (metres and miles) - the default.
#DISTANCE_UNITS = 'british'

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
                        #phone_formatter=my_custom_function,
                        
                        # Whether or not results from the LDAP server should be
                        # sorted alphabetically by surname
                        #alphabetical=True,
                        
                        # Determines the LDAP query passed to the server,
                        # using {surname} and {forename} as substitutes for the
                        # user to search for
                        #query='(sn={surname})',
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

            # Provider used to provide real-time information for buses, scraped from
            # a website powered by CloudAmber solutions.
            #Provider('molly.apps.places.providers.cloudamber.CloudAmberBusRtiProvider',
            #    url = 'http://www.oxontime.com',
            #),
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
                            #control_number_key='1032',
                            
                            # Optional - the encoding which is used on results
                            # from the server, only unicode or marc8 are
                            # supported. Aleph supplies unicode, and marc8 is
                            # default
                            #results_encoding='unicode',
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
        
        # This specifies which tabs are created for different transport entity
        # types. It is a dictionary where the key represents the slug of the
        # pagewhich contains it, and the value is a tuple of type slug (i.e.,
        # from http://example.com/places/category/TYPE-SLUG/) and the number to
        # show by default
        nearby = {
            
            # This shows the 5 nearest bus stops
            'bus': ('bus-stop', 5),
            
            # This shows the 3 nearest Supertram stops
            #'supertram': ('supertram-stop', 3),
            
            # This shows the 3 nearest Tube stations
            #'tube': ('tube-station', 3),
        },
        
        # The nearby pages above can be augmented with a "status" provider which
        # typically shows information about the different lines currently on
        # that transit network. These settings are called TYPE_status_provider,
        # where the first word (TYPE) is replaced with the key of the nearby
        # page as defined in the setting above
        #
        # Molly comes with a single provider for transit line statuses, which is
        # the London Underground line statuses. Using the example setting above,
        # where Tube stations are exposed with the key 'tube', the following
        # setting will show the current Tube status on the 'tube' page:
        #tube_status_provider = 'molly.apps.transport.providers.TubeStatusProvider',
        
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
    
    # The tours app allows for users to build their own walking tours of a city
    # or University by choosing their own points of interest from a list
    # presented to them. Tours displays metadata stored with an entity in the
    # places database depending on the type of tour that is created. For more
    # information, see http://docs.mollyproject.org/dev/ref/apps/tours.html.
    #Application('molly.apps.tours', 'tours', 'Tours',
    #            
    #            # The types setting defines the different "types" of tours that
    #            # can be created. The tour type determines which descriptions
    #            # are shown to people on the tour, as well as what categories
    #            # of entities are shown to the user when creating the tour.
    #            types={
    #                
    #                # The dictionary key refers to the 'slug' of the tour
    #                # creation page (e.g., /tours/*admissions*/create/) and should
    #                # be all lower case with only letters, - or numbers
    #                'admissions': {
    #                    
    #                    # This is the name of the tour as shown to users. If you
    #                    # are using i18n, you will want to manually add this
    #                    # string to your custom .po files to ensure it is
    #                    # correctly translated
    #                    'name': 'Admissions tour',
    #                    
    #                    # This is a list of entity types which are shown to the
    #                    # user, and should consist of slugs for the EntityType.
    #                    'attraction_types': ['department', 'hall-of-residence'],
    #                    
    #                    # This next setting is optional, and if set, will
    #                    # suggest particular entities to the user (as defined by
    #                    # identifier scheme and value in the same form as is
    #                    # used in entity URLs) if the user will be passing by
    #                    # them.
    #                    'suggested_entities': ['oxpoints:23233759'],
    #                },
    #                
    #                # To create more types, simply copy and paste the template
    #                # above in this list.
    #            },
    #            
    #            # This setting defines the points where visitors can arrive to
    #            # start their tours
    #            arrival_points=[
    #                    # scheme:value, is_park_and_ride, park_and_ride_routes
    #                    
    #                    # The first value is the identifier scheme and value for
    #                    # the arrival point, the second is whether or not this
    #                    # is Park & Ride site (in which case, users will
    #                    # continue to their tour starting point by bus) and the
    #                    # final defines which bus routes serve that point, if
    #                    # that point is a Park & Ride site
    #                    
    #                    # This example defines the arrival point of Oxford rail
    #                    # station which is a non-Park&Ride site
    #                    ('crs:OXF', False, []),
    #                    
    #                    # This example defines the arrival point of a Park&Ride
    #                    # which is served by the bus route 300.
    #                    ('osm:W4333225', True, ['300']),
    #                ],
    #            
    #            # This setting defines the long distance routes (e.g., coach
    #            # services) that can be used to access the University.
    #            arrival_routes=[
    #                    
    #                    # The first element is the service ID (which should
    #                    # match up with a route in the places database) and then
    #                    # a human-readable name for that route.
    #                    ('TUBE', 'Oxford Tube'),
    #                    ('X90', 'Oxford Espress (X90)'),
    #                    ('X70', 'Gatwick Airline (X70)'),
    #                    ('X80', 'Heathrow Airline (X80)'),
    #                ],
    #            
    #            # This optional setting which defines how far that suggested
    #            # entities should be looked for off the currently plotted route
    #            # e.g., with the default setting of 100 metres, then if any
    #            # suggested entities are within 100 metres of the route the user
    #            # would be walking anyway, then those entities are suggested to
    #            # the user
    #            suggestion_distance = 100,
    #
    #),

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
            Provider('molly.apps.feeds.providers.RSSFeedsProvider'),
            Provider('molly.apps.feeds.providers.ICalFeedsProvider'),
            Provider('molly.apps.feeds.providers.TalksCamFeedsProvider'),
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

                # All parameters are optional but search_around and search_distance
                # are highly recommended
                # Central point of the search area.
                search_around = (-1.25821, 51.75216),
                # Radius of the search area. (distance in meters)
                search_distance = 20000,
                # Make a second call to the API to retrieve the name of the
                # area, for each search result
                get_area = True,
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
    
    # This app provides utilities to other apps which want to generate a route
    # between 2 points
    Application('molly.routing', 'routing', 'Routing',
        display_to_user = False,
    ),

]

# This is where any non-Molly apps are added to the configuration
INSTALLED_APPS = extract_installed_apps(APPLICATIONS) + INSTALLED_APPS
