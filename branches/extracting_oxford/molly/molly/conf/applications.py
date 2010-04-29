from __future__ import with_statement

from threading import Lock

from django.conf import settings as django_settings

import settings

__all__ = [
    'app_by_local_name',
    'app_by_application_name',
    'apps_by_application_name',
    'all_apps',
    'applications',
]

_load_lock = Lock()
_loaded = False
_by_local_name = {}
_by_application_name = {}
_all = []

def _require_loaded_apps(f):
    def g(*args, **kwargs):
        if not _loaded:
            _load_apps()
        return f(*args, **kwargs)
    return g

def _load_apps():
    global _loaded, _all
    with _load_lock:
        if _loaded:
            return
        _loaded = True

        for application in django_settings.APPLICATIONS:
            app = application.get()
            _by_local_name[app.local_name] = app
            if not app.application_name in _by_application_name:
                _by_application_name[app.application_name] = []
            _by_application_name[app.application_name].append(app)
            _all.append(app)
        _all = tuple(_all)

@_require_loaded_apps
def app_by_local_name(local_name):
    return _by_local_name[local_name]

@_require_loaded_apps
def app_by_application_name(application_name):
    return _by_application_name[application_name][0]

@_require_loaded_apps
def apps_by_application_name(application_name):
    return list(_by_application_name[application_name])

@_require_loaded_apps
def all_apps():
    return _all

class Applications(object):
    def __getattr__(self, key):
        return app_by_local_name(key)
    __getitem__ = __getattr__

applications = Applications()
