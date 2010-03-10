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
    def data(cls, request, context, *args, **kwargs):
        return breadcrumb_func(cls, request, context, *args, **kwargs)
    
    def render(cls, request, context, *args, **kwargs):
        breadcrumb = data(cls, request, context, *args, **kwargs)
        
        if breadcrumb.parent:
            parent_data = breadcrumb.parent(cls, request, context)
            parent = parent_data.title, parent_data.url()
        else:
            parent = None
        
        index = resolve(reverse('%s:index' % breadcrumb.application))[0].breadcrumb.data(cls, request, context)
        index = index.title, index.url()
        
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
    
    return classmethod(render)

def NullBreadcrumb(cls, request, context, *args, **kwargs):
    return None

def lazy_reverse(view_name, *args, **kwargs):
    def f():
        return reverse(view_name, *args, **kwargs)
    return f
    
def static_reverse(path):
    def f():
        return path
    return f
    
def lazy_parent(view, *args, **kwargs):
    def f(cls, request, context):
        return view.breadcrumb.data(cls, request, context, *args, **kwargs)
    return f

def static_parent(path, title, application=None):
    def f(cls, request, context):
        return Breadcrumb(
            application, None, title, lambda: path
        )
    return f
    
