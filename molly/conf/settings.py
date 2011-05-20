import imp

from django.utils.importlib import import_module
from django.conf.urls.defaults import include as urlconf_include
from django.core.urlresolvers import RegexURLResolver, RegexURLPattern

"""
Provides a framework for Molly application objects.

An Application object wraps a Django application, and allows Molly to
extend an application with configuration information, and add extra base
classes to views to mix-in deployment-specific functionality.
"""

# This module does a lot of dynamically creating class objects using the
# second form of the 'type' function.[0]
#
# [0] http://docs.python.org/library/functions.html#type

class ApplicationConf(object):
    pass

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
        for key in kwargs.copy():
            if key == 'provider':
                self.providers += (kwargs.pop(key),)
            elif key.endswith('provider'):
                self.providers += (kwargs[key],)

    def get(self):
        if self.conf:
            return self.conf

        providers = []
        for provider in self.providers:
            if isinstance(provider, Provider):
                providers.append(provider())
            else:
                providers.append(Provider(provider)())

        bases = tuple(base() for base in self.extra_bases)
        if self.secure:
            from molly.auth.views import SecureView
            bases = (SecureView,) + bases

        self.kwargs.update({
            'application_name': self.application_name,
            'local_name': self.local_name,
            'title': self.title,
            'providers': providers,
            'provider': providers[-1] if len(providers) else None,
            'urls': self._get_urls_property(bases),
            'has_urlconf': self._module_exists(self.urlconf),
        })
        
        # Handle "other" providers - i.e., singletons which end with
        # 'provider' and perhaps provide specialised providers
        for key in self.kwargs:
            if key != 'provider' and key.endswith('provider'):
                provider = self.kwargs[key]
                if not isinstance(provider, Provider):
                    provider = Provider(provider)
                providers.append(provider())
                self.kwargs[key] = provider()
        self.conf = type(self.local_name.capitalize()+'Conf', (ApplicationConf,), self.kwargs)()

        for provider in self.conf.providers:
            provider.conf = self.conf

        self.conf.display_to_user = self.kwargs['display_to_user'] and self.kwargs['has_urlconf']

        # Configure any logging for this application, passing the
        # configuration lest it needs it.
        try:
            logconfig = import_module(self.application_name + '.logconfig')
        except ImportError, e:
            pass
        else:
            logconfig.configure_logging(self.conf)

        return self.conf

    def add_conf_to_pattern(self, pattern, conf, bases):
        """
        Coalesces an Application's configuration with the views in its urlconf.

        Takes a RegexURLPattern or RegexURLResolver, a conf object and a tuple
        of extra base classes to inherit from. Returns an object of the same
        type as its first argument with callbacks replaced with new views using
        conf and bases.
        """

        # Don't import at module scope as this module will be imported from a
        # settings file.
        from molly.utils.views import BaseView

        if isinstance(pattern, RegexURLResolver):
            # Recurse through the patterns
            patterns = []
            for subpattern in pattern.url_patterns:
                patterns.append(self.add_conf_to_pattern(subpattern, conf, bases))
            # Create a new RegexURLResolver with the new patterns
            return RegexURLResolver(pattern.regex.pattern, # The regex pattern string
                                    patterns,
                                    pattern.default_kwargs,
                                    pattern.app_name,
                                    pattern.namespace)
        elif isinstance(pattern, RegexURLPattern):
            # Get the callback and make sure it derives BaseView
            callback = pattern.callback
            if not issubclass(callback, BaseView):
                return callback
            
            if bases:
                # Create a new callback with the extra bases
                callback = type(callback.__name__ + 'Extended', (callback,) + bases, {})
                callback.__module__ = pattern.callback.__module__
            
            # Instantiate the callback with the conf object
            callback = callback(conf)
                
            # Transplant this new callback into a new RegexURLPattern, keeping
            # the same regex, default_args and name.
            return RegexURLPattern(pattern.regex.pattern,
                                   callback,
                                   pattern.default_args,
                                   pattern.name)
        else:
            raise TypeError("Expected RegexURLResolver or RegexURLPattern instance, got %r." % type(pattern))

    def _get_urls_property(self, bases):
        """
        Returns a property object that will load and cache the urlconf for an app.

        This will add base classes to the views as necessary and pass the conf to
        each view instance.
        """

        @property
        def urls(conf):
            if hasattr(conf, '_urls_cache'):
                return conf._urls_cache
            # Load the urls module and extract the patterns
            urlpatterns = import_module(self.urlconf).urlpatterns
            new_urlpatterns = []
            for pattern in urlpatterns:
                # Call to recursively apply the conf and bases to each of the
                # views referenced in the urlconf.
                new_urlpatterns.append(self.add_conf_to_pattern(pattern, self.conf, bases))
            conf._urls_cache = urlconf_include(new_urlpatterns, self.application_name.split('.')[-1], self.local_name)
            return conf._urls_cache
        return urls
    
    def _module_exists(self, module_name):
        """
        Returns True iff module_name exists (but isn't necessarily importable).
        """

        # imp.find_module doesn't handle hierarchical module names, so we split
        # on full stops and keep feeding it the path it returns until we run
        # out of module name.

        module_name, path = module_name.split('.'), None
        while module_name:
            try:
                path = [imp.find_module(module_name.pop(0), path)[1]]
            except ImportError, e:
                return False
        return True

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

class Provider(object):
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
