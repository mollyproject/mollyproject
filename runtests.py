#This file mainly exists to allow python setup.py test to work.
import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'molly.conf.test_settings'

from django.test.utils import get_runner
from django.conf import settings


def runtests():
    from south.management.commands import patch_for_test_db_setup
    patch_for_test_db_setup()
    test_runner = get_runner(settings)
    test_runner = test_runner(interactive=True, verbosity=1, failfast=False)
    failures = test_runner.run_tests([])
    sys.exit(bool(failures))

if __name__ == '__main__':
    runtests()
