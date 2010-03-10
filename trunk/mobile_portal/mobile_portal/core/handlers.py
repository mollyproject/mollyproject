from inspect import isfunction
import traceback, time, simplejson
from django.http import HttpResponse


class ViewMetaclass(type):
    def __new__(cls, name, bases, dict):
        for key, value in dict.items():
            if isfunction(value) and key != '__new__':
                dict[key] = classmethod(value)
        return type.__new__(cls, name, bases, dict)

class BaseView(object):
    __metaclass__ = ViewMetaclass
    
    def method_not_acceptable(cls, request):
        response = HttpResponse(
            'You may not perform a %s request against this resource.' % request.method.upper(),
            status=405,
        )
        return response
        
    def bad_request(cls, request):
        response = HttpResponse(
            'Your request was malformed.',
            status=400,
        )
        return response
        
    def initial_context(cls, request, *args, **kwargs):
        return {}
        
    def __new__(cls, request, *args, **kwargs):
        method_name = 'handle_%s' % request.method
        if hasattr(cls, method_name):
            context = cls.initial_context(request, *args, **kwargs)
            context['breadcrumbs'] = cls.breadcrumb.render(cls, request, context, *args, **kwargs)
            response = getattr(cls, method_name)(request, context, *args, **kwargs)
            return response
        else:
            return cls.method_not_acceptable(request)
            
    def get_zoom(cls, request, default=16):
        try:
            zoom = int(request.GET['zoom'])
        except (ValueError, KeyError):
            zoom = default
        else:
            zoom = min(max(10, zoom), 18)
        return zoom
        
    def json_response(cls, data):
        return HttpResponse(simplejson.dumps(data), mimetype="application/json")
        
class ZoomableView(BaseView):
    default_zoom = None
    
    def initial_context(cls, request, *args, **kwargs):
        try:
            zoom = int(request.GET['zoom'])
        except (KeyError, ValueError):
            zoom = cls.default_zoom
        else:
            zoom = min(max(10, zoom), 18)
        return {
            'zoom': zoom,
        }
        
