from __future__ import with_statement

from threading import Lock

from django.conf import settings as django_settings

__all__ = [
    'app_by_local_name',
    'app_by_application_name',
    'apps_by_application_name',
    'all_apps',
    'get_app',
    'applications',
    'has_app_by_local_name',
    'has_app_by_application_name',
    'has_app',
]

_load_lock = Lock()
_by_local_name = {}
_by_application_name = {}

def _require_loaded_apps(f):
    def g(*args, **kwargs):
        if not _loaded:
            _load_apps()
        return f(*args, **kwargs)
    return g

def _load_app(filter_func):
    with _load_lock:
        for application in django_settings.APPLICATIONS:
            if not filter_func(application):
                continue
            app = application.get()
            _by_local_name[app.local_name] = app
            if not app.application_name in _by_application_name:
                _by_application_name[app.application_name] = []
            _by_application_name[app.application_name].append(app)

def app_by_local_name(local_name):
    try:
        return _by_local_name[local_name]
    except KeyError:
        _load_app(lambda app: app.local_name == local_name)
        return _by_local_name[local_name]

def app_by_application_name(application_name):
    try:
        return _by_application_name[application_name][0]
    except KeyError:
        _load_app(lambda app: app.application_name == application_name)
        return _by_application_name[application_name][0]

def apps_by_application_name(application_name):
    try:
        return _by_application_name[application_name]
    except KeyError:
        _load_app(lambda app: app.application_name == application_name)
        return _by_application_name[application_name]

def get_app(application_name=None, local_name=None):
    if local_name:
        return app_by_local_name(local_name)
    else:
        return app_by_application_name(application_name)

def all_apps():
    return [app.get() for app in django_settings.APPLICATIONS]

def has_app_by_application_name(application_name):
    try:
        app_by_application_name(application_name)
    except KeyError:
        return False
    else:
        return True

def has_app_by_local_name(local_name):
    try:
        app_by_local_name(local_name)
    except KeyError:
        return False
    else:
        return True

def has_app(application_name=None, local_name=None):
    if local_name:
        return has_app_by_local_name(local_name)
    else:
        return has_app_by_application_name(application_name)

class Applications(object):
    def __getattr__(self, key):
        return app_by_local_name(key)
    __getitem__ = __getattr__

applications = Applications()
