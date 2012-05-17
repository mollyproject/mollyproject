#!/usr/bin/env python
import os
import sys
from os.path import dirname, abspath
from unittest2 import defaultTestLoader
from molly.conf import default_settings as settings
from django.core.management import setup_environ

sys.path.insert(0, dirname(abspath(__file__)))


os.environ['DJANGO_SETTINGS_MODULE'] = 'molly.conf.default_settings'
setup_environ(settings)
from django.test.utils import setup_test_environment
setup_test_environment()


def runtests():
    __main__ = sys.modules['__main__']
    setupDir = os.path.abspath(os.path.dirname(__main__.__file__))
    return defaultTestLoader.discover(setupDir)

if __name__ == '__main__':
    runtests()
