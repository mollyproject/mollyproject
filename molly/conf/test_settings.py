from molly.commands.site_template.settings import *
from os import path

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'molly',
        'USER': 'postgres'
    }
}

TEST_RUNNER = 'discover_runner.DiscoverRunner'
TEST_DISCOVER_TOP_LEVEL = path.dirname(path.dirname(__file__))
TEST_DISCOVER_ROOT = TEST_DISCOVER_TOP_LEVEL
