from inspect import isfunction
import simplejson, logging
from datetime import datetime, date
from xml.etree import ElementTree as ET

from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.paginator import Paginator
from django.contrib.gis.geos import Point
from django.core.urlresolvers import reverse, resolve, NoReverseMatch
from django.conf import settings

logger = logging.getLogger('core.requests')

from time import clock as time_clock
import sys

class timing(object):
    def __new__(cls, f, *args, **kwargs):
        t1 = time_clock()
        value = f(*args, **kwargs)
        t2 = time_clock()
        frame = sys._getframe()
        print "TIME %s:%d %2.4f %s" % (__file__, frame.f_lineno, t2-t1, f.__name__)
        return value


class DateUnicode(unicode): pass
class DateTimeUnicode(unicode): pass

def renderer(format, mimetypes=None):
    """
    Decorates a view method to say that it renders a particular format and mimetypes.

    Use as:
        @renderer(format="foo")
        def render_foo(self, request, context, template_name): ...
    or
        @renderer(format="foo", mimetypes=("application/x-foo",))
        def render_foo(self, request, context, template_name): ...

    The former case will inherit mimetypes from the previous renderer for that
    format in the MRO. Where there isn't one, it will default to the empty
    tuple.
    """

    def g(f):
        f.is_renderer = True
        f.format = format
        f.mimetypes = mimetypes
        return f
    return g


import types

class ViewMetaclass(type):
    def __new__(cls, name, bases, dict):

        # Pull the renderers from the bases into a couple of new dicts for
        # this views renderers
        formats_by_mimetype = {}
        formats = {}
        for base in reversed(bases):
            if hasattr(base, 'FORMATS'):
                formats.update(base.FORMATS)
                formats_by_mimetype.update(base.FORMATS_BY_MIMETYPE)

        for key, value in dict.items():
            # If the method is a renderer we add it to our dicts. We can't add
            # the functions right now because we want them bound to the class
            # object that hasn't yet been created. Instead, add the keys (strs)
            # and we'll replace them with the bound classmethods later.
            if isfunction(value) and getattr(value, 'is_renderer', False):
                if value.mimetypes is not None:
                    mimetypes = value.mimetypes
                elif value.format in formats:
                    mimetypes = formats[value.format].mimetypes
                else:
                    mimetypes = ()
                for mimetype in mimetypes:
                    formats_by_mimetype[mimetype] = key
                formats[value.format] = key

        dict.update({
            'FORMATS': formats,
            'FORMATS_BY_MIMETYPE': formats_by_mimetype,
        })

        # Create our view.
        view = type.__new__(cls, name, bases, dict)

        return view



class BaseView(object):
    __metaclass__ = ViewMetaclass

    ALLOWABLE_METHODS = ('GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS', 'PUT')

    def method_not_allowed(self, request):
        return HttpResponseNotAllowed([m for m in self.ALLOWABLE_METHODS if hasattr(self, 'handle_%s' % m)])

    def not_acceptable(self, request):
        response = HttpResponse("The desired media type is not supported for this resource.", mimetype="text/plain")
        response.status_code = 406
        return response

    def bad_request(self, request):
        response = HttpResponse(
            'Your request was malformed.',
            status=400,
        )
        return response

    def initial_context(self, request, *args, **kwargs):
        return {}
    
    def __new__(cls, conf, *args, **kwargs):
        if isinstance(conf, HttpRequest):
            return cls(None)(conf, *args, **kwargs)
        else:
            return object.__new__(cls, conf, *args, **kwargs)

    def __init__(self, conf=None):
        self.conf = conf
    
    def __unicode__(self):
        cls = type(self)
        return ".".join((cls.__module__, cls.__name__))

    def __call__(self, request, *args, **kwargs):
        method_name = 'handle_%s' % request.method
        if hasattr(self, method_name):
            context = self.initial_context(request, *args, **kwargs)
            context['breadcrumbs'] = self.breadcrumb(request, context, *args, **kwargs)
            response = getattr(self, method_name)(request, context, *args, **kwargs)
            return response
        else:
            return self.method_not_allowed(request)

    def handle_HEAD(self, request, *args, **kwargs):
        """
        Provides a default HEAD handler that strips the content from the
        response returned by the GET handler.
        """
        if hasattr(self, 'handle_GET'):
            response = self.handle_GET(request, *args, **kwargs)
        else:
            response = self.method_not_acceptable(request)
        response.content = ''
        return response

    def get_zoom(self, request, default=16):
        try:
            zoom = int(request.GET['zoom'])
        except (ValueError, KeyError):
            zoom = default
        else:
            zoom = min(max(10, zoom), 18)
        return zoom

    def render(self, request, context, template_name):
        if request.REQUEST.get('format') in self.FORMATS:
            renderer = self.FORMATS[request.REQUEST['format']]
        elif 'format' in request.REQUEST:
            return self.not_acceptable(request)
        #elif request.is_ajax():
        #    renderer = self.FORMATS['json']
        elif request.META.get('HTTP_ACCEPT'):
            accepts = [a.split(';')[0].strip() for a in request.META['HTTP_ACCEPT'].split(',')]
            for accept in accepts:
                # WebKit's Accept header is broken. See
                # http://www.newmediacampaigns.com/page/webkit-team-admits-accept-header-error
                # and https://bugs.webkit.org/show_bug.cgi?id=27267
                if accept in ('application/xml', 'text/xml') and ' AppleWebKit/' in request.META.get('HTTP_USER_AGENT', ''):
                    continue
                if accept in self.FORMATS_BY_MIMETYPE:
                    renderer = self.FORMATS_BY_MIMETYPE[accept]
                    try:
                        return getattr(self, renderer)(request, context, template_name)
                    except NotImplementedError:
                        pass
            else:
                response = HttpResponse("""\
Your Accept header didn't contain any supported media ranges.

Supported ranges are:

 * %s\n""" % '\n * '.join(f for f in self.FORMATS), mimetype="text/plain" )
                response.status_code = 406 # Not Acceptable
                return response
        else:
            renderer = self.FORMATS['html']

        renderer = getattr(self, renderer)

        # Stop external sites from grabbing JSON representations of pages
        # which contain sensitive user information.
        offsite_referrer = 'HTTP_REFERER' in request.META and request.META['HTTP_REFERER'].split('/')[2] != request.META.get('HTTP_HOST')
        if renderer.format != 'html' and context.get('exposes_user_data') and offsite_referrer:
            return HttpResponseForbidden("This page cannot be requested with an off-site Referer", mimetype="text/plain")
        context.pop('exposes_user_data', None)

        try:
            return renderer(request, context, template_name)
        except NotImplementedError:
            return self.not_acceptable(request)


    def render_to_format(self, request, context, template_name, format):
        render_method = self.FORMATS[format]
        return render_method(request, context, template_name)

    @renderer(format="json", mimetypes=('application/json',))
    def render_json(self, request, context, template_name):
        context = self.simplify_value(context)
        return HttpResponse(simplejson.dumps(context), mimetype="application/json")

    @renderer(format="js", mimetypes=('text/javascript','application/javascript',))
    def render_js(self, request, context, template_name):
        callback = request.GET.get('callback', request.GET.get('jsonp', 'callback'))
        content = simplejson.dumps(self.simplify_value(context))
        content = "%s(%s);" % (callback, content)
        return HttpResponse(content, mimetype="application/javascript")

    @renderer(format="html", mimetypes=('text/html', 'application/xhtml+xml', '*/*'))
    def render_html(self, request, context, template_name):
        if template_name is None:
            raise NotImplementedError
        return render_to_response(template_name+'.html',
                                  context, context_instance=RequestContext(request),
                                  mimetype='text/html')

    @renderer(format="xml", mimetypes=('application/xml', 'text/xml'))
    def render_xml(self, request, context, template_name):
        context = self.simplify_value(context)
        return HttpResponse(ET.tostring(self.serialize_to_xml(context), encoding='UTF-8'), mimetype="application/xml")

    @renderer(format="yaml", mimetypes=('application/x-yaml',))
    def render_yaml(self, request, context, template_name):
        try:
            import yaml
        except ImportError:
            raise NotImplementedError

        context = self.simplify_value(context)
        return HttpResponse(yaml.safe_dump(context), mimetype="application/x-yaml")

    @renderer(format="fragment")
    def render_fragment(self, request, context, template_name):
        '''Uses block rendering functions, see end of file.'''
        if template_name is None:
            raise NotImplementedError
        body = render_block_to_string(template_name + '.html', 'body', context, RequestContext(request))
        title = render_block_to_string(template_name + '.html', 'title', context, RequestContext(request))
        content = render_block_to_string(template_name + '.html', 'content', context, RequestContext(request))
        return HttpResponse(simplejson.dumps({'body': body, 'title': title, 'content': content}), mimetype="application/json")

    def simplify_value(self, value):
        if hasattr(value, 'simplify_for_render'):
            return value.simplify_for_render(self.simplify_value, self.simplify_model)
        elif isinstance(value, dict):
            out = {}
            for key in value:
                new_key = key if isinstance(key, (basestring, int)) else str(key)
                try:
                    out[new_key] = self.simplify_value(value[key])
                except NotImplementedError:
                    pass
            return out
        elif isinstance(value, (list, tuple, set, frozenset)):
            out = []
            for subvalue in value:
                try:
                    out.append(self.simplify_value(subvalue))
                except NotImplementedError:
                    pass
            if isinstance(value, tuple):
                return tuple(out)
            else:
                return out
        elif isinstance(value, (basestring, int, float)):
            return value
        elif isinstance(value, datetime):
            return DateTimeUnicode(value.isoformat(' '))
        elif isinstance(value, date):
            return DateUnicode(value.isoformat())
        elif hasattr(type(value), '__mro__') and models.Model in type(value).__mro__:
            return self.simplify_model(value)
        elif isinstance(value, Paginator):
            return self.simplify_value(value.object_list)
        elif value is None:
            return None
        elif isinstance(value, Point):
            return self.simplify_value(list(value))
        elif hasattr(value, '__iter__'):
            return [self.simplify_value(item) for item in value]
        else:
            raise NotImplementedError

    XML_DATATYPES = (
        (DateUnicode, 'date'),
        (DateTimeUnicode, 'datetime'),
        (str, 'string'),
        (unicode, 'string'),
        (int, 'integer'),
        (float, 'float'),
    )

    def simplify_model(self, obj, terse=False):
        if obj is None:
            return None
        # It's a Model instance
        if hasattr(obj._meta, 'expose_fields'):
            expose_fields = obj._meta.expose_fields
        else:
            expose_fields = [f.name for f in obj._meta.fields]
        out = {
            '_type': '%s.%s' % (obj.__module__[:-7], obj._meta.object_name),
            '_pk': obj.pk,
        }
        if hasattr(obj, 'get_absolute_url'):
            out['_url'] = obj.get_absolute_url()
        if terse:
            out['_terse'] = True
        else:
            for field_name in expose_fields:
                if field_name in ('password',):
                    continue
                try:
                    value = getattr(obj, field_name)
                    if hasattr(type(value), '__bases__') and models.Model in type(value).__bases__:
                        value = self.simplify_model(value, terse=True)
                    out[field_name] = self.simplify_value(value)
                except NotImplementedError:
                    pass
        return out

    def serialize_to_xml(self, value):
        if value is None:
            node = ET.Element('null')
        elif isinstance(value, bool):
            node = ET.Element('literal')
            node.text = 'true' if value else 'false'
            node.attrib['type'] = 'boolean'
        elif isinstance(value, (basestring, int, float)):
            node = ET.Element('literal')
            node.text = unicode(value)
            node.attrib['type'] = [d[1] for d in self.XML_DATATYPES if isinstance(value, d[0])][0]
        elif isinstance(value, dict):
            if '_type' in value:
                node = ET.Element('object', {'type': value['_type'], 'pk': unicode(value.get('_pk', ''))})
                del value['_type']
                del value['_pk']
                if '_url' in value:
                    node.attrib['url'] = value['_url']
                    del value['_url']
                if value.get('_terse'):
                    node.attrib['terse'] = 'true'
                    del value['_terse']
            else:
                node = ET.Element('collection', {'type': 'mapping'})
            for key in value:
                v = self.serialize_to_xml(value[key])
                subnode = ET.Element('item', {'key':key})
                subnode.append(v)
                node.append(subnode)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for x,y in ((list, 'list'), (tuple, 'tuple')):
                if isinstance(value, x):
                    node = ET.Element('collection', {'type': y})
                    break
            else:
                node = ET.Element('collection', {'type':'set'})
            for item in value:
                v = self.serialize_to_xml(item)
                subnode = ET.Element('item')
                subnode.append(v)
                node.append(subnode)
        else:
            node = ET.Element('unknown')

        return node


class ZoomableView(BaseView):
    default_zoom = None

    def initial_context(self, request, *args, **kwargs):
        try:
            zoom = int(request.GET['zoom'])
        except (KeyError, ValueError):
            zoom = self.default_zoom
        else:
            zoom = min(max(10, zoom), 18)
        return {
            'zoom': zoom,
        }

# FIXME:
#       Block rendering methods, from http://djangosnippets.org/942
#       Will need tidying up and fitting for the style of annotation we end up with
#       We need it to render and output multiple blocks in one go, obviously, for
#       efficiency.
#       But for the moment, it'll do?

from django.template.loader_tags import BlockNode, ExtendsNode
from django.template import loader, Context, RequestContext, TextNode

class BlockNotFound(Exception):
    pass


def render_template_block(template, block, context):
    """
    Renders a single block from a template. This template should have previously been rendered.
    """
    return render_template_block_nodelist(template.nodelist, block, context)

def render_template_block_nodelist(nodelist, block, context):
    for node in nodelist:
        if isinstance(node, BlockNode) and node.name == block:
            return node.render(context)
        for key in ('nodelist', 'nodelist_true', 'nodelist_false'):
            if hasattr(node, key):
                try:
                    return render_template_block_nodelist(getattr(node, key), block, context)
                except:
                    pass
    for node in nodelist:
        if isinstance(node, ExtendsNode):
            try:
                return render_template_block(node.get_parent(context), block, context)
            except BlockNotFound:
                pass
    raise BlockNotFound

def render_block_to_string(template_name, block, dictionary=None, context_instance=None):
    """
    Loads the given template_name and renders the given block with the given dictionary as
    context. Returns a string.
    """
    dictionary = dictionary or {}
    t = loader.get_template(template_name)
    if context_instance:
        context_instance.update(dictionary)
    else:
        context_instance = Context(dictionary)
    t.render(context_instance)
    return render_template_block(t, block, context_instance)

def ReverseView(request):
    from molly.auth.views import SecureView

    try:
        name = request.GET['name']
        args = request.GET.getlist('arg')
        
        path = reverse(name, args=args)
        view, view_args, view_kwargs = resolve(path)
        is_secure = issubclass(view, SecureView) and not settings.DEBUG_SECURE
        return HttpResponse("http%s://%s%s" % (
            's' if is_secure else '',
            request.META['HTTP_HOST'],
            path,
        ), mimetype='text/plain')
    except NoReverseMatch:
        raise Http404
    except KeyError:
        return HttpResponseBadRequest()
