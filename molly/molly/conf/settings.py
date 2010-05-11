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
        self.conf = None
        
        kwargs['display_to_user'] = kwargs.get('display_to_user', True)

        self.providers = kwargs.pop('providers', ())
        if 'provider' in kwargs:
            self.providers += (kwargs.pop('provider'),)

    def get(self):
        if self.conf:
            return self.conf

        from molly.utils.views import BaseView, SecureView

        providers = []
        for provider in self.providers:
            if isinstance(provider, SimpleProvider):
                providers.append(provider())
            else:
                providers.append(SimpleProvider(provider)())
        try:
            import_module(self.urlconf)
        except ImportError:
            urls = None
        else:
            urls = urlconf_include(self.urlconf, self.application_name.split('.')[-1], self.local_name)

        self.kwargs.update({
            'application_name': self.application_name,
            'local_name': self.local_name,
            'title': self.title,
            'providers': providers,
            'provider': providers[-1] if len(providers) else None,
            'urls': urls,
            'display_to_user': self.kwargs['display_to_user'] and (urls is not None),
        })
        self.conf = type(self.local_name.capitalize()+'Conf', (object,), self.kwargs)

        try:
            views_module = import_module(self.application_name+'.views')
        except ImportError:
            views_module = None
        else:
            bases = tuple(base() for base in self.extra_bases)
            if self.secure:
                bases = (SecureView,) + bases

            bar = dir(views_module)
            for n in dir(views_module):
                view = getattr(views_module, n)
                if not isinstance(view, type) or not BaseView in view.__mro__ or view is BaseView or view.__dict__.get('abstract'):
                    continue

                view.conf = self.conf
                view.__bases__ = bases + view.__bases__

        return self.conf

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
    def __init__(self, klass, **kwargs):
        self.klass, self.kwargs = klass, kwargs

    def __call__(self):
        try:
            return self._provider
        except:
            mod_name, cls_name = self.klass.rsplit('.', 1)
            module = import_module(mod_name)
            klass = getattr(module, cls_name)
            self._provider = klass(**self.kwargs)
            self._provider.class_path = self.klass
            return self._provider

def batch(cron_stmt, initial_metadata={}):
    def g(f):
        f.is_batch = True
        f.cron_stmt = cron_stmt
        f.initial_metadata = initial_metadata
        return f
    return g
