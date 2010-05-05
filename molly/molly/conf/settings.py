from django.utils.importlib import import_module
from django.conf.urls.defaults import include as urlconf_include

class Application(object):
    

    def __init__(self, application_name, local_name, title, **kwargs):
        self.application_name, self.local_name = application_name, local_name
        self.title = title
        
        self.authentication = kwargs.pop('authentication', None)
        self.secure = kwargs.pop('secure', False)
        self.extra_bases = kwargs.pop('extra_bases', ())
        self.urlconf = kwargs.pop('urlconf', application_name+'.urls')
        self.kwargs = kwargs
        self.batches = []
        self.app = None
        
        kwargs['display_to_user'] = kwargs.get('display_to_user', True)

        self.providers = kwargs.pop('providers', ())
        if 'provider' in kwargs:
            self.providers += (kwargs.pop('provider'),)

    def get(self):
        if self.app:
            return self.app

        from molly.utils.views import BaseView, SecureView
        views_module = import_module(self.application_name+'.views')

        providers = []
        for provider in self.providers:
            if isinstance(provider, SimpleProvider):
                providers.append(provider())
                for batch in provider.batches:
                    self.batches.append((
                        batch.times, getattr(providers[-1], batch.method_name),
                        batch.args, batch.kwargs
                    ))
            else:
                providers.append(SimpleProvider(provider)())

        self.kwargs['application_name'] = self.application_name
        self.kwargs['local_name'] = self.local_name
        self.kwargs['providers'] = providers
        self.kwargs['provider'] = providers[-1] if len(providers) else None
        conf = type(self.local_name.capitalize()+'Config', (object,), self.kwargs)

        bases = tuple(base() for base in self.extra_bases)
        if self.secure:
            bases = (SecureView,) + bases

        bar = dir(views_module)
        for n in dir(views_module):
            view = getattr(views_module, n)
            if not isinstance(view, type) or not BaseView in view.__mro__ or view is BaseView or view.__dict__.get('abstract'):
                continue

            view.conf = conf
            view.__bases__ = bases + view.__bases__
            print view, view.__bases__

        self.app = type(self.local_name.capitalize()+'App', (object,), {
            'urls': urlconf_include(self.urlconf, self.application_name.split('.')[-1], self.local_name),
            'application_name': self.application_name,
            'local_name': self.local_name,
            'title': self.title,
            'conf': conf,
        })
        return self.app

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
        base = type(cls_name, (klass,), self.kwargs)
        base.__module__ = mod_name
        return base

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

def batch(cron_stmt):
    def g(f):
        f.is_batch = True
        f.cron_stmt = cron_stmt
        return f
    return g
