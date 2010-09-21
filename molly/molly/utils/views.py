from inspect import isfunction
import logging, itertools
from datetime import datetime, date

import simplejson
from lxml import etree

from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse, resolve, NoReverseMatch
from django.conf import settings

logger = logging.getLogger('core.requests')

from .http import MediaType
from .simplify import simplify_value, simplify_model, serialize_to_xml

def renderer(format, mimetypes=(), priority=0):
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

    Takes an optional priority argument to resolve ties between renderers.
    """

    def g(f):
        f.is_renderer = True
        f.format = format
        f.mimetypes = set(MediaType(mimetype, priority) for mimetype in mimetypes)
        return f
    return g

class ViewMetaclass(type):
    def __new__(cls, name, bases, dict):

        # Pull the renderers from the bases into a couple of new dicts for
        # this view's renderers
        formats_by_mimetype = {}
        formats = {}
        for base in reversed(bases):
            if hasattr(base, 'FORMATS'):
                formats.update(base.FORMATS)
                formats_by_mimetype.update(base.FORMATS_BY_MIMETYPE)

        for key, value in dict.items():
            # If the method is a renderer we add it to our dicts. We can't add
            # the functions right now because we want them bound to the view
            # instance that hasn't yet been created. Instead, add the keys (strs)
            # and we'll replace them with the bound instancemethods in BaseView.__init__.
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
        
        # Resolve renderer names to bound instancemethods. Also turn the
        # FORMATS_BY_MIMETYPE dict into a list of pairs ordered by descending priority.
        self.FORMATS = dict((key, getattr(self, value)) for key, value in self.FORMATS.items())
        formats_sorted = sorted(self.FORMATS_BY_MIMETYPE.items(), key=lambda x: x[0].priority, reverse=True)
        self.FORMATS_BY_MIMETYPE = tuple((key, getattr(self, value)) for (key, value) in formats_sorted)
    
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
        context.pop('exposes_user_data', None)

        if request.REQUEST.get('format') in self.FORMATS:
            renderers = [self.FORMATS[request.REQUEST['format']]]
        elif 'format' in request.REQUEST:
            return self.not_acceptable(request)
        elif request.META.get('HTTP_ACCEPT'):
            accepts = self.parse_accept_header(request.META['HTTP_ACCEPT'])
            renderers = MediaType.resolve(accepts, self.FORMATS_BY_MIMETYPE)
        else:
            renderers = [self.FORMATS['html']]

        # Stop external sites from grabbing JSON representations of pages
        # which contain sensitive user information.
        offsite_referrer = 'HTTP_REFERER' in request.META and request.META['HTTP_REFERER'].split('/')[2] != request.META.get('HTTP_HOST')

        for renderer in renderers:
            if renderer.format != 'html' and context.get('exposes_user_data') and offsite_referrer:
                continue
            try:
                return renderer(request, context, template_name)
            except NotImplementedError:
                continue
        else:
            tried_mimetypes = list(itertools.chain(*[r.mimetypes for r in renderers]))
            response = HttpResponse("""\
Your Accept header didn't contain any supported media ranges.

Supported ranges are:

 * %s\n""" % '\n * '.join(sorted('%s (%s)' % (f[0].value, f[1].format) for f in self.FORMATS_BY_MIMETYPE if not f[0] in tried_mimetypes)), mimetype="text/plain")
            response.status_code = 406 # Not Acceptable
            return response

    def parse_accept_header(cls, accept):
        media_types = []
        for media_type in accept.split(','):
            try:
                media_types.append(MediaType(media_type))
            except ValueError:
                pass
        return media_types

    def render_to_format(self, request, context, template_name, format):
        render_method = self.FORMATS[format]
        return render_method(request, context, template_name)

    @renderer(format="json", mimetypes=('application/json',))
    def render_json(self, request, context, template_name):
        context = simplify_value(context)
        return HttpResponse(simplejson.dumps(context), mimetype="application/json")

    @renderer(format="js", mimetypes=('text/javascript','application/javascript',))
    def render_js(self, request, context, template_name):
        callback = request.GET.get('callback', request.GET.get('jsonp', 'callback'))
        content = simplejson.dumps(simplify_value(context))
        content = "%s(%s);" % (callback, content)
        return HttpResponse(content, mimetype="application/javascript")

    @renderer(format="html", mimetypes=('text/html', 'application/xhtml+xml'), priority=1)
    def render_html(self, request, context, template_name):
        if template_name is None:
            raise NotImplementedError
        return render_to_response(template_name+'.html',
                                  context, context_instance=RequestContext(request),
                                  mimetype='text/html')

    @renderer(format="xml", mimetypes=('application/xml', 'text/xml'))
    def render_xml(self, request, context, template_name):
        context = simplify_value(context)
        return HttpResponse(etree.tostring(serialize_to_xml(context), encoding='UTF-8'), mimetype="application/xml")

    # We don't want to depend on YAML. If it's there offer it as a renderer, otherwise ignore it.
    try:
        __import__('yaml') # Try importing, but don't stick the result in locals.
        @renderer(format="yaml", mimetypes=('application/x-yaml',), priority=-1)
        def render_yaml(self, request, context, template_name):
            import yaml
            context = simplify_value(context)
            return HttpResponse(yaml.safe_dump(context), mimetype="application/x-yaml")
    except ImportError, e:
        pass

    @renderer(format="fragment")
    def render_fragment(self, request, context, template_name):
        '''Uses block rendering functions, see end of file.'''
        if template_name is None:
            raise NotImplementedError
        body = render_block_to_string(template_name + '.html', 'body', context, RequestContext(request))
        title = render_block_to_string(template_name + '.html', 'title', context, RequestContext(request))
        content = render_block_to_string(template_name + '.html', 'content', context, RequestContext(request))
        return HttpResponse(simplejson.dumps({'body': body, 'title': title, 'content': content}), mimetype="application/json")



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
