from inspect import isfunction
import traceback, time, simplejson, logging
from datetime import datetime

from django.db import models
from django.http import HttpResponse, HttpResponseNotAllowed
from django.template import TemplateDoesNotExist, RequestContext
from django.shortcuts import render_to_response

logger = logging.getLogger('core.requests')

class ViewMetaclass(type):
    def __new__(cls, name, bases, dict):
        for key, value in dict.items():
            if isfunction(value) and key != '__new__':
                dict[key] = classmethod(value)
        return type.__new__(cls, name, bases, dict)

class BaseView(object):
    __metaclass__ = ViewMetaclass
    
    ALLOWABLE_METHODS = ('GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS', 'PUT')
    
    def method_not_acceptable(cls, request):
        return HttpResponseNotAllowed([m for m in cls.ALLOWABLE_METHODS if hasattr(cls, 'handle_%s' % m)])
        
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
            context['breadcrumbs'] = cls.breadcrumb(request, context, *args, **kwargs)
            response = getattr(cls, method_name)(request, context, *args, **kwargs)
            return response
        else:
            return cls.method_not_acceptable(request)
                

            
    def handle_HEAD(cls, request, *args, **kwargs):
        """
        Provides a default HEAD handler that strips the content from the
        response returned by the GET handler.
        """
        if hasattr(cls, 'handle_GET'):
            response = cls.handle_GET(request, *args, **kwargs)
        else:
            response = cls.method_not_acceptable(request)
        response.content = ''
        return response
            
    def get_zoom(cls, request, default=16):
        try:
            zoom = int(request.GET['zoom'])
        except (ValueError, KeyError):
            zoom = default
        else:
            zoom = min(max(10, zoom), 18)
        return zoom
        
    FORMATS = (
        # NAME, MIMETYPE
        ('rdf', 'application/rdf+xml'),
        ('html', 'text/html'),
        ('json', 'application/json'),
        ('yaml', 'application/x-yaml'),
        ('xml', 'application/xml'),
    )
    
    FORMATS_BY_NAME = dict(FORMATS)
    FORMATS_BY_MIMETYPE = dict((y,x) for (x,y) in FORMATS)
        
    def render(cls, request, context, template_name):
        if request.GET.get('format') in cls.FORMATS_BY_NAME:
            format = request.GET['format']
        elif request.META.get('HTTP_ACCEPT'):
            accepts = [a.split(';')[0].strip() for a in request.META['HTTP_ACCEPT'].split(',')]
            for accept in accepts:
                if accept in cls.FORMATS_BY_MIMETYPE:
                    format = cls.FORMATS_BY_MIMETYPE[accept]
                    try:
                        return cls.render_to_format(request, context, template_name, format)
                    except (TemplateDoesNotExist, NotImplementedError):
                        pass
            else:
                response = HttpResponse("""\
Your Accept header didn't contain any supported media ranges.

Supported ranges are:

 * %s\n""" % '\n * '.join(f for f in cls.FORMATS_BY_NAME), mimetype="text/plain" )
                response.status_code = 406 # Not Acceptable
                return response
        else:
            format = 'html'
            
        try:
            return cls.render_to_format(request, context, template_name, format)
        except (TemplateDoesNotExist, NotImplementedError):
            response = HttpResponse("The desired media type is not supported for this resource.", mimetype="text/plain")
            response.status_code = 406
            return response
    
    def render_to_format(cls, request, context, template_name, format):
        render_method = getattr(cls, 'render_%s' % format)
        return render_method(request, context, template_name)

    def render_json(cls, request, context, template_name):
        context = cls.simplify_context(context)
        return HttpResponse(simplejson.dumps(context), mimetype="application/json")
        
    def render_html(cls, request, context, template_name):
        return render_to_response(template_name+'.html',
                                  context, context_instance=RequestContext(request),
                                  mimetype='text/html')
    
    def render_rdf(cls, request, context, template_name):
        raise NotImplementedError
        
    def render_xml(cls, request, context, template_name):
        return render_to_response(template_name+'.xml',
                                  context, context_instance=RequestContext(request),
                                  mimetype='application/xml')

    def render_yaml(cls, request, context, template_name):
        try:
            import yaml
        except ImportError:
            raise NotImplementedError
            
        context = cls.simplify_context(context)
        return HttpResponse(yaml.dump(context), mimetype="application/x-yaml")

    def simplify_context(cls, context):
        if isinstance(context, dict):
            out = {}
            for key in context:
                try:
                    out[key] = cls.simplify_context(context[key])
                except NotImplementedError:
                    pass
            return out
        elif isinstance(context, (list, tuple, set, frozenset)):
            out = []
            for value in context:
                try:
                    out.append(cls.simplify_context(value))
                except NotImplementedError:
                    pass
            if isinstance(context, tuple):
                return tuple(out)
            else:
                return out
        elif isinstance(context, (basestring, int, float)):
            return context
        elif isinstance(context, datetime):
            return context.isoformat(' ')
        elif hasattr(type(context), '__bases__') and models.Model in type(context).__bases__:
            # It's a Model instance
            if hasattr(context._meta, 'expose_fields'):
                expose_fields = context._meta.expose_fields
            else:
                expose_fields = [f.name for f in context._meta.fields]
            out = {
                '_type': '.'.join(context._meta.app_label, context._meta.object_name),
                '_pk': context.pk,
            }
            for field_name in expose_fields:
                try:
                    value = getattr(context, field_name)
                    if hasattr(type(value), '__bases__') and models.Model in type(value).__bases__:
                        value = {
                            '_type': '.'.join(value._meta.app_label, value._meta.object_name),
                            '_pk': value.pk,
                        }
                    out[field_name] = cls.simplify_context(value)
                except NotImplementedError:
                    pass
            return out
        elif hasattr(context, 'simplify'):
            return context.simplify(cls.simplify_context)
        else:
            raise NotImplementedException
            
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

class SecureView(BaseView):
    pass
