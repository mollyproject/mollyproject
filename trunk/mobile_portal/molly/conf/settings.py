from django.utils.importlib import import_module
class Application(object):
    registry = {}

    def __init__(self, app, name, **kwargs):
        self.app, self.name = app, name
        self.authentication = kwargs.pop('authentication', None)
        self.secure = kwargs.pop('secure', False)
        self.extra_bases = kwargs.pop('extra_bases', ())
        self.urlconf = kwargs.pop('urlconf', app+'.urls')
        self.kwargs = kwargs

        self.providers = kwargs.pop('providers', ())
        if 'provider' in kwargs:
            self.providers += (kwargs.pop('provider'),)

        self.registry[name] = self

    @classmethod
    def get(cls, name):
        app = cls.registry[name]

        from molly.utils.views import BaseView, SecureView
        views_module = import_module(app.app+'.views')

        providers = []
        for provider in app.providers:
            if isinstance(provider, SimpleProvider):
                providers.append(provider())
            else:
                providers.append(SimpleProvider(provider)())

        app.kwargs['providers'] = providers
        app.kwargs['provider'] = providers[-1] if len(providers) else None
        conf = type(app.name.capitalize()+'Config', (object,), app.kwargs)

        bases = tuple(base() for base in app.extra_bases)
        if app.secure:
            bases = (SecureView,) + bases

        for n in dir(views_module):
            view = getattr(views_module, n)
            if not isinstance(view, type) or not BaseView in view.__bases__:
                continue

            view.conf = conf
            view.__bases__ = bases + view.__bases__

        return type(app.name.capitalize()+'App', (object,), {
            'urls': (app.urlconf, app.app, app.name),
        })

class Authentication(object):
    def __init__(klass, **kwargs):
        pass

class ExtraBase(object):
    def __init__(self, klass, **kwargs):
        self.klass, self.kwargs = klass, kwargs

    def __call__(self):
        module = import_module(self.klass)
        return type(module.__name__, module, self.kwargs)

def extract_installed_apps(applications):
    return tuple(app.app for app in applications)

def Secret(name):
    pass

class SimpleProvider(object):
    def __init__(self, klass=None, **kwargs):
        self.klass, self.kwargs = klass, kwargs

    def __call__(self):
        if self.klass:
            mod_name, cls_name = self.klass.rsplit('.', 1)
            module = import_module(mod_name)
            klass = getattr(module, cls_name)
            return klass(**self.kwargs)
        else:
            return type('SimpleProvider', (object,), self.kwargs)

