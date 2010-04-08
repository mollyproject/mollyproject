from django.utils.importlib import import_module
from django.conf.urls.defaults import include as urlconf_include

class Application(object):
    registry = {}

    def __init__(self, application_name, local_name, title, **kwargs):
        self.application_name, self.local_name = application_name, local_name
        self.title = title
        
        self.authentication = kwargs.pop('authentication', None)
        self.secure = kwargs.pop('secure', False)
        self.extra_bases = kwargs.pop('extra_bases', ())
        self.urlconf = kwargs.pop('urlconf', application_name+'.urls')
        self.kwargs = kwargs
        self.batches = []
        
        kwargs['display_to_user'] = kwargs.get('display_to_user', True)

        self.providers = kwargs.pop('providers', ())
        if 'provider' in kwargs:
            self.providers += (kwargs.pop('provider'),)

        self.registry[local_name] = self

    @classmethod
    def get(cls, local_name):
        app = cls.registry[local_name]
        app.kwargs['local_name'] = local_name

        from molly.utils.views import BaseView, SecureView
        views_module = import_module(app.application_name+'.views')

        providers = []
        for provider in app.providers:
            if isinstance(provider, SimpleProvider):
                providers.append(provider())
                for batch in provider.batches:
                    app.batches.append((
                        batch.times, getattr(providers[-1], batch.method_name),
                        batch.args, batch.kwargs
                    ))
            else:
                providers.append(SimpleProvider(provider)())

        app.kwargs['application_name'] = app.application_name
        app.kwargs['providers'] = providers
        app.kwargs['provider'] = providers[-1] if len(providers) else None
        conf = type(app.local_name.capitalize()+'Config', (object,), app.kwargs)

        bases = tuple(base() for base in app.extra_bases)
        if app.secure:
            bases = (SecureView,) + bases

        for n in dir(views_module):
            view = getattr(views_module, n)
            if not isinstance(view, type) or not BaseView in view.__bases__:
                continue

            view.conf = conf
            view.__bases__ = bases + view.__bases__

        return type(app.local_name.capitalize()+'App', (object,), {
            'urls': urlconf_include(app.urlconf, app.application_name.split('.')[-1], app.local_name),
            'application_name': app.application_name,
            'local_name': app.local_name,
            'title': app.title,
            'conf': conf,
        })

class Authentication(object):
    def __init__(klass, **kwargs):
        pass

class ExtraBase(object):
    def __init__(self, klass, **kwargs):
        self.klass, self.kwargs = klass, kwargs

    def __call__(self):
        mod_name, cls_name = self.klass.rsplit('.', 1)
        module = import_module(mod_name)
        klass = getattr(module, cls_name)
        return type(module.__name__, (klass,), self.kwargs)

def extract_installed_apps(applications):
    return tuple(app.application_name for app in applications)

class SimpleProvider(object):
    def __init__(self, klass=None, **kwargs):
        self.batches = tuple(kwargs.pop('batches', ()))
        self.batches += (kwargs.pop('batch'),) if 'batch' in kwargs else ()
        self.klass, self.kwargs = klass, kwargs

    def __call__(self):
        if self.klass:
            mod_name, cls_name = self.klass.rsplit('.', 1)
            module = import_module(mod_name)
            klass = getattr(module, cls_name)
            return klass(**self.kwargs)
        else:
            return type('SimpleProvider', (object,), self.kwargs)

class Batch(object):
    def __init__(self, method_name, args=[], kwargs={}, **times):
        self.method_name, self.times = method_name, times
        self.args, self.kwargs = args, kwargs
