from django.conf import settings as django_settings

import settings

class Applications(dict):
    def __getattr__(self, local_name):
        try:
            return dict.__getitem__(self, local_name)
        except KeyError:
            self[local_name] = settings.Application.get(local_name)
            return self[local_name]
    __getitem__ = __getattr__

    def __iter__(self):
        return iter([app.local_name for app in django_settings.APPLICATIONS])
    
    def values(self):
        return [self[app] for app in self]
