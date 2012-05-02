# default_settings.py: Default Django settings that it makes sense to apply
# across all installations.

# This refers to Django's 'Site' framework, which Molly does not use. It is
# recommended to leave this at its default setting
SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# When set, then a version number is added to compressed files, this means
# changing a file also changes its URL - when combined with far future expires,
# then this solves caching issues
PIPELINE_VERSION = True

# We set this to False for a performance optimisation - we don't want CSS and JS
# to be regenerated on the server, just once at deploy time. If you do want
# this, then change it to True
PIPELINE_AUTO = False

# This list is used to specifiy which classes are used to help Django find
# templates to be rendered. In most circumstances, there is no reason to change
# this
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader', # First try the templates in the directories specified by TEMPLATE_DIRS
    'django.template.loaders.app_directories.Loader', # Then try the ones that come with the bundled apps
    'molly.utils.template_loaders.MollyDefaultLoader' # Finally, use Molly's molly_default virtual directory
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

# This list specifies which Django middleware clases are used when processing
# requests and responses. For more information about Django middleware, please
# see https://docs.djangoproject.com/en/dev/topics/http/middleware/
# The defaults are fine for most installs
MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware', # This enables Django's cross-site request forgery protection framework
    'molly.wurfl.middleware.WurflMiddleware', # This enables Molly's device detection capability (required)
    'django.middleware.common.CommonMiddleware', # This incorporates some convenience functions from Django (required)
    'django.contrib.sessions.middleware.SessionMiddleware', # This enables Django's session storage framework (required)
    'molly.utils.middleware.LocationMiddleware', # This annotates requests with a user_location attribute
    'molly.utils.middleware.CookieLocaleMiddleware', # This enables i18n support in Molly (required)
    'molly.utils.middleware.ErrorHandlingMiddleware', # This enables Molly's error handling and reporting framework
    'django.contrib.auth.middleware.AuthenticationMiddleware', # This allows for users to be logged in in Django (required)
    'molly.auth.middleware.SecureSessionMiddleware', # This adds the capability to have secure sessions (sessions which are HTTPS only)
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

INSTALLED_APPS = (
    'django.contrib.auth', # Django's user authentication system
    'django.contrib.admin', # Django's admin backend
    'django.contrib.contenttypes', # Django's Content Types API - this is a prerequisite for the admin interface
    'django.contrib.sessions', # Django's sessions API - this is required
    'django.contrib.sites', # Django's sites API, this is a prerequisite for the comments API
    'django.contrib.gis', # Geodjango - this is required
    'django.contrib.comments', # Django's comments API - used in the feature vote app
    'django.contrib.staticfiles', # Staticfiles handles media for Molly
    'pipeline', # Pipeline is an external library that minifies JS and CSS
    'south', # South handles changes to database schema
    'djcelery', # Celery tasks run our periodic batch processing
)

# Don't do South migrations when running unit tests - just do a syncdb
# See http://south.aeracode.org/docs/settings.html#south-tests-migrate
SOUTH_TESTS_MIGRATE = False
