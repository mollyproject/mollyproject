from django.core.urlresolvers import reverse, resolve

__all__ = [
    'Breadcrumb', 'BreadcrumbFactory', 'NullBreadcrumb',
    'lazy_reverse', 'lazy_parent'
]

class Breadcrumb(object):
    def __init__(self, application, parent, title, url):
        self.application, self.title, self.url = application, title, url
        self.parent = parent

def BreadcrumbFactory(breadcrumb_func):
    def f(cls, request, context, *args, **kwargs):
        return breadcrumb_func(cls, request, context, *args, **kwargs)
    
    def render(cls, request, context, *args, **kwargs):
        breadcrumb = f(cls, request, context, *args, **kwargs)
        
        if breadcrumb.parent:
            parent = breadcrumb.parent(request, context)
            parent = parent.title, parent.url()
        else:
            parent = None
        
        index = resolve(reverse('%s_index' % breadcrumb.application))[0].breadcrumb(request, context)
        index = index.title, index.url()
        
        parent_is_index = index == parent
        
        return (
            breadcrumb.application,
            index,
            parent,
            parent_is_index,
            breadcrumb.title,
        )
        
    f.render = render
    f.breadcrumb_func = breadcrumb_func
    
    return classmethod(f)

class NullBreadcrumb:
    @classmethod
    def render(cls, request, context, *args, **kwargs):
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
    def f(request, context):
        return view.breadcrumb(request, context, *args, **kwargs)
    return f
