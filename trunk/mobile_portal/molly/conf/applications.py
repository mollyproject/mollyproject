import settings

class Applications(dict):
    def __getattr__(self, name):
        try:
            return dict.__getitem__(self, name)
        except KeyError:
            self[name] = settings.Application.get(name)
            return self[name]
    __getitem__ = __getattr__

    def __iter__(self):
        return iter(settings.Application.registry)
