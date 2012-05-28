#This file mainly exists to allow python setup.py test to work.
import os
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'molly.conf.test_settings'
test_dir = os.path.dirname(__file__)
sys.path.insert(0, test_dir)

from django.test.utils import get_runner
from django.conf import settings


def runtests():
    test_runner = get_runner(settings)()
    failures = test_runner.run_tests([], interactive=True, verbosity=1)
    sys.exit(failures)

if __name__ == '__main__':
    runtests()
