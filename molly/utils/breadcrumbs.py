from django.core.urlresolvers import reverse, resolve

import inspect

__all__ = [
    'Breadcrumb', 'BreadcrumbFactory', 'NullBreadcrumb',
    'lazy_reverse', 'lazy_parent'
]

class Breadcrumb(object):
    def __init__(self, application, parent, title, url):
        self.application, self.title, self.url = application, title, url
        self.parent = parent

def BreadcrumbFactory(breadcrumb_func):
    def data(self, request, context, *args, **kwargs):
        return breadcrumb_func(self, request, context, *args, **kwargs)
    
    def render(self, request, context, *args, **kwargs):
        breadcrumb = data(self, request, context, *args, **kwargs)
        
        if breadcrumb.parent:
            parent_data = breadcrumb.parent(self, breadcrumb.application, request, context)
            parent = parent_data.title, parent_data.url(parent_data.application)
        else:
            parent = None
        
        index_view = resolve(reverse('%s:index' % breadcrumb.application))[0]
        index = index_view.breadcrumb.data(index_view, request, context)
        index = index.title, index.url(breadcrumb.application)
        
        parent_is_index = index == parent
        
        return (
            breadcrumb.application,
            index,
            parent,
            parent_is_index,
            breadcrumb.title,
        )
        
    render.data = data
    render.breadcrumb_func = breadcrumb_func

    return render

@staticmethod
def NullBreadcrumb(request, context, *args, **kwargs):
    return None

def lazy_reverse(view_name, *args, **kwargs):
    def f(application_name):
        view = view_name
        if ':' not in view:
            view = '%s:%s' % (application_name, view)
        return reverse(view, *args, **kwargs)
    return f
    
def static_reverse(path):
    def f():
        return path
    return f
    
def lazy_parent(view_name, *args, **kwargs):
    def f(self, application_name, request, context):
        view = view_name
        if ':' not in view:
            view = '%s:%s' % (application_name, view)
        view, view_args, view_kwargs = resolve(reverse(view, args=args, kwargs=kwargs))
        return view.breadcrumb.data(view, request, context, *view_args, **view_kwargs)
    return f

def static_parent(path, title, application=None):
    def f(self, app, request, context):
        return Breadcrumb(
            application, None, title, lambda app: path
        )
    return f
    
