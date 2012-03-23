from email.utils import formatdate
from time import mktime
from inspect import isfunction
import logging
import itertools
from datetime import datetime, timedelta
from slimmer.slimmer import xhtml_slimmer
from urlparse import urlparse, urlunparse, parse_qs
from urllib import urlencode

import simplejson
from lxml import etree

from django.http import (HttpRequest, HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotAllowed, Http404,
                         HttpResponseRedirect, HttpResponsePermanentRedirect)
from django.template import loader, Context, RequestContext
from django.template.loader_tags import BlockNode, ExtendsNode
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse, resolve, NoReverseMatch
from django.conf import settings
from django.utils.translation import ugettext as _
from django.views.debug import technical_500_response
from django.middleware.csrf import get_token

logger = logging.getLogger(__name__)

from molly.utils.http import MediaType, HttpResponseSeeOther
from molly.utils.simplify import (simplify_value, serialize_to_xml)
from molly.utils.breadcrumbs import NullBreadcrumb

def renderer(format, mimetypes=(), priority=0):
    """
    Decorates a view method to say that it renders a particular format and
    mimetypes.

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
        f.mimetypes = set(MediaType(mimetype, priority)
                          for mimetype in mimetypes)
        return f
    return g

def tidy_query_string(url):
    scheme, netloc, path, params, query, fragment = urlparse(url)
    args = []
    for k, vs in parse_qs(query, keep_blank_values=True).items():
        if k in ['format', 'language_code']:
            continue
        else:
            for v in vs:
                args.append((k.encode('utf-8'), v.encode('utf-8')))
    query = urlencode(args)
    return urlunparse((scheme, netloc, path, params, query, fragment))

class ViewMetaclass(type):
    def __new__(mcs, name, bases, attrs):

        # Pull the renderers from the bases into a couple of new dicts for
        # this view's renderers
        formats_by_mimetype = {}
        formats = {}
        for base in reversed(bases):
            if hasattr(base, 'FORMATS'):
                formats.update(base.FORMATS)
                formats_by_mimetype.update(base.FORMATS_BY_MIMETYPE)

        for key, value in attrs.items():
            # If the method is a renderer we add it to our dicts. We can't add
            # the functions right now because we want them bound to the view
            # instance that hasn't yet been created. Instead, add the keys
            # (strs) and we'll replace them with the bound instancemethods in
            # BaseView.__init__.
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

        attrs.update({
            'FORMATS': formats,
            'FORMATS_BY_MIMETYPE': formats_by_mimetype,
        })

        # Create our view.
        view = type.__new__(mcs, name, bases, attrs)

        return view


class BaseView(object):
    __metaclass__ = ViewMetaclass

    ALLOWABLE_METHODS = ('GET', 'POST', 'DELETE', 'HEAD', 'OPTIONS', 'PUT')

    breadcrumb = NullBreadcrumb

    def method_not_allowed(self, request):
        return HttpResponseNotAllowed([m for m in self.ALLOWABLE_METHODS
                                       if hasattr(self, 'handle_%s' % m)])

    def not_acceptable(self, request):
        response = HttpResponse(
            _("The desired media type is not supported for this resource."),
            mimetype="text/plain")
        response.status_code = 406
        return response

    def bad_request(self, request):
        response = HttpResponse(
            _('Your request was malformed.'),
            status=400)
        return response

    def initial_context(self, request, *args, **kwargs):
        return {}
    
    def __new__(self, conf, *args, **kwargs):
        if isinstance(conf, HttpRequest):
            return self(None)(conf, *args, **kwargs)
        else:
            return object.__new__(self, conf, *args, **kwargs)

    def __init__(self, conf=None):
        self.conf = conf
        
        # Resolve renderer names to bound instancemethods. Also turn the
        # FORMATS_BY_MIMETYPE dict into a list of pairs ordered by descending
        # priority.
        self.FORMATS = dict((key, getattr(self, value))
                            for key, value in self.FORMATS.items())
        formats_sorted = sorted(self.FORMATS_BY_MIMETYPE.items(),
                                key=lambda x: x[0].priority,
                                reverse=True)
        self.FORMATS_BY_MIMETYPE = tuple((key, getattr(self, value))
                                         for (key, value) in formats_sorted)
    
    def __unicode__(self):
        self = type(self)
        return ".".join((self.__module__, self.__name__))

    def __call__(self, request, *args, **kwargs):
        method_name = 'handle_%s' % request.method
        if hasattr(self, method_name):
            context = self.initial_context(request, *args, **kwargs)
            context['breadcrumbs'] = self.breadcrumb(request, context,
                                                     *args, **kwargs)
            response = getattr(self, method_name)(request, context,
                                                  *args, **kwargs)
            return response
        else:
            return self.method_not_allowed(request)

    def handle_HEAD(self, request, context, *args, **kwargs):
        """
        Provides a default HEAD handler that strips the content from the
        response returned by the GET handler.
        """
        if hasattr(self, 'handle_GET'):
            response = self.handle_GET(request, context, *args, **kwargs)
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

    def redirect(self, uri, request, type='found'):
        """
        When called, returns a response which redirects users to the correct
        locations. It also correctly handles redirects within the AJAX page
        transition framework. The first argument is the URI to be redirected to,
        the second the request object and the third is optional, and specifies
        the type of redirect to be done:
        
        * found (the default) is a standard 302 Found redirect
        * perm is a standard 301 Moved Permanently redirect
        * seeother is a standard 303 See Other redirect
        * secure is a 301 Moved Permanently redirect, that has a special meaning
          when used within the AJAX framework, which causes pages to manually
          redirect to the new URL, rather than just AJAX transition. This causes
          transitions to/from secure pages to work as expected.
        """
        if 'format' in request.REQUEST:
            uri = urlparse(uri)
            args = []
            for k, vs in parse_qs(uri.query, keep_blank_values=True).items():
                if k == 'format':
                    continue
                else:
                    for v in vs:
                        args.append((k, v))
            if (uri.netloc != request.META.get('HTTP_HOST') and \
                uri.netloc != '') or type == 'secure':
                # This makes sure we never cross http/https boundaries with AJAX
                # requests or try to make an off-site AJAX request
                uri = urlunparse((uri.scheme, uri.netloc, uri.path, uri.params,
                                  urlencode(args), uri.fragment))
                return self.render(request, {'redirect': uri}, None)
            args.append(('format', request.REQUEST['format']))
            uri = urlunparse((uri.scheme, uri.netloc, uri.path, uri.params,
                              urlencode(args), uri.fragment))
        
        redirect = {
            'found': HttpResponseRedirect,
            'perm': HttpResponsePermanentRedirect,   
            'secure': HttpResponsePermanentRedirect,
            'seeother': HttpResponseSeeOther,
        }.get(type)
        return redirect(uri)

    def render(self, request, context, template_name, expires=None):
        """
        Given a request, a context dictionary and a template name, this renders
        the template with the given context according to the capabilities and
        requested format of the client. An optional final argument is that of
        a timedelta object, which sets additional caching headers for the
        content.
        """
        context.pop('exposes_user_data', None)

        if 'format' in request.REQUEST:
            formats = request.REQUEST['format'].split(',')
            renderers, seen_formats = [], set()
            for format in formats:
                if format in self.FORMATS and format not in seen_formats:
                    renderers.append(self.FORMATS[format])
        elif request.META.get('HTTP_ACCEPT'):
            accepts = self.parse_accept_header(request.META['HTTP_ACCEPT'])
            renderers = MediaType.resolve(accepts, self.FORMATS_BY_MIMETYPE)
        else:
            renderers = [self.FORMATS['html']]

        # Stop external sites from grabbing JSON representations of pages
        # which contain sensitive user information.
        try:
            offsite_referrer = 'HTTP_REFERER' in request.META and \
                request.META['HTTP_REFERER'].split('/')[2] != \
                                                request.META.get('HTTP_HOST')
        except IndexError:
            # Malformed referrers (i.e., those not containing a full URL) throw
            # this
            offsite_referrer = True

        for renderer in renderers:
            if renderer.format != 'html' and context.get('exposes_user_data') \
              and offsite_referrer:
                continue
            try:
                response = renderer(request, context, template_name)
            except NotImplementedError:
                continue
            else:
                if expires is not None and not settings.DEBUG and \
                  not getattr(settings, 'NO_CACHE', False):
                    response['Expires'] = formatdate(
                        mktime((datetime.now() + expires).timetuple()))
                    
                    # if expires is negative, then consider this to be no-cache
                    if expires < timedelta(seconds=0):
                        response['Cache-Control'] = 'no-cache'
                    else:
                        response['Cache-Control'] = 'max-age=%d' % \
                                (expires.seconds + expires.days * 24 * 3600)
                    
                return response
        else:
            if 'format' not in request.REQUEST:
                tried_mimetypes = list(itertools.chain(*[r.mimetypes
                                                         for r in renderers]))
                response = HttpResponse(
                  _("Your Accept header didn't contain any supported media ranges.") + \
                  "\n\n" + _("Supported ranges are:") + \
                  "\n\n * %s\n" % '\n * '.join(
                      sorted('%s (%s)' % (f[0].value, f[1].format) for f in
                      self.FORMATS_BY_MIMETYPE if not f[0] in tried_mimetypes)),
                mimetype="text/plain")
            else:
                response = HttpResponse(
                  _("Unable to render this document in this format.") + "\n\n" +
                  _("Supported formats are") + ":\n\n * %s\n" \
                                % '\n * '.join(self.FORMATS.keys()),
                  mimetype="text/plain")
            response.status_code = 406 # Not Acceptable
            return response

    def parse_accept_header(self, accept):
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
        resolved = resolve(request.path)
        context['view_name'] = '%s:%s' % (
            self.conf.application_name.split('.')[-1], resolved.url_name)
        
        # Include CSRF token, as templates don't get rendered csrf_token is
        # never called which breaks CSRF for apps written against the JSON API
        get_token(request)
        
        return HttpResponse(simplejson.dumps(context),
                            mimetype="application/json")

    @renderer(format="js", mimetypes=('text/javascript',
                                      'application/javascript',))
    def render_js(self, request, context, template_name):
        callback = request.GET.get('callback',
                                   request.GET.get('jsonp', 'callback'))
        content = simplejson.dumps(simplify_value(context))
        content = "%s(%s);" % (callback, content)
        return HttpResponse(content, mimetype="application/javascript")

    @renderer(format="html", mimetypes=('text/html', 'application/xhtml+xml'),
              priority=1)
    def render_html(self, request, context, template_name):
        if template_name is None:
            raise NotImplementedError
        return render_to_response(
            template_name+'.html',
            context,
            context_instance=RequestContext(request, current_app=self.conf.local_name),
            mimetype='text/html;charset=UTF-8')

    @renderer(format="xml", mimetypes=('application/xml', 'text/xml'))
    def render_xml(self, request, context, template_name):
        context = simplify_value(context)
        return HttpResponse(
            etree.tostring(serialize_to_xml(context), encoding='UTF-8'),
            mimetype="application/xml")

    # We don't want to depend on YAML. If it's there offer it as a renderer,
    # otherwise ignore it.
    try:
        # Try importing, but don't stick the result in locals.
        __import__('yaml')
        @renderer(format="yaml", mimetypes=('application/x-yaml',), priority=-1)
        def render_yaml(self, request, context, template_name):
            import yaml
            context = simplify_value(context)
            return HttpResponse(yaml.safe_dump(context),
                                mimetype="application/x-yaml")
    except ImportError, e:
        pass

    @renderer(format="fragment")
    def render_fragment(self, request, context, template_name):
        """
        Uses block rendering functions, see end of file.
        """
        if template_name is None:
            if 'redirect' in context:
                return HttpResponse(
                    simplejson.dumps({
                        'redirect': request.build_absolute_uri(
                            context['redirect'])
                    }),
                    mimetype="application/json")
            raise NotImplementedError
        body = render_blocks_to_string(template_name + '.html', context,
                                       RequestContext(request))
        
        uri = tidy_query_string(request.get_full_path())
        
        try:
            title = xhtml_slimmer(body['whole_title'])
        except:
            logger.warn('Slimmer failed to slim title', exc_info=True)
            title = body['whole_title']
        
        try:
            pagebody = xhtml_slimmer(body['body'])
        except:
            logger.warn('Slimmer failed to slim body', exc_info=True)
            pagebody = body['body']
        
        return HttpResponse(
            simplejson.dumps({
                'uri': uri,
                'body': pagebody,
                'title': title,
            }),
            mimetype="application/json")

class ZoomableView(BaseView):
    default_zoom = None

    def initial_context(self, request, *args, **kwargs):
        context = super(ZoomableView, self).initial_context(request,
                                                            *args, **kwargs)
        try:
            zoom = int(request.GET['zoom'])
        except (KeyError, ValueError):
            zoom = self.default_zoom
        else:
            zoom = min(max(10, zoom), 18)
        context['zoom'] = zoom
        context.update({
            'zoom_controls': True,
        })
        return context

def render_template_blocks(template, context, extensions={}):
    """
    Renders all the blocks from a template and returns a dictionary of block
    names and results.
    
    This template should have previously been rendered.
    """
    return render_template_nodelist(template.nodelist, context)

def render_template_nodelist(nodelist, context, extensions={}):
    blocks = {}
    for node in nodelist:
        if isinstance(node, ExtendsNode):
            blocks.update(render_template_blocks(node.get_parent(context),
                                                 context))
        if isinstance(node, BlockNode):
            # Render this node and add it to dictionary
            blocks[node.name] = node.render(context)
        for key in ('nodelist', 'nodelist_true', 'nodelist_false'):
            # Descend any recursive nodes
            if hasattr(node, key):
                blocks.update(render_template_nodelist(getattr(node, key),
                                                       context))
    return blocks

def render_blocks_to_string(template_name, dictionary=None,
                            context_instance=None):
    """
    Loads the given template_name and renders all blocks with the given
    dictionary as context. Returns a dictionary of blocks to string.
    """
    dictionary = dictionary or {}
    t = loader.get_template(template_name)
    if context_instance:
        context_instance.update(dictionary)
    else:
        context_instance = Context(dictionary)
    t._render(context_instance)
    return render_template_blocks(t, context_instance)

def ReverseView(request):
    from molly.auth.views import SecureView

    try:
        name = request.GET['name']
        args = request.GET.getlist('arg')
        
        path = reverse(name, args=args)
        view, view_args, view_kwargs = resolve(path)
        is_secure = isinstance(view, SecureView) and not settings.DEBUG_SECURE
        return HttpResponse("http%s://%s%s" % (
            's' if is_secure else '',
            request.META['HTTP_HOST'],
            path,
        ), mimetype='text/plain')
    except NoReverseMatch:
        raise Http404
    except KeyError:
        return HttpResponseBadRequest()

def handler500(request, exc_info=None):
    
    context = {
        'request': request,
    }

    if exc_info and (request.user.is_superuser or settings.DEBUG):
        # Now try and return this as a redirect if we're using fragment rendering
        if request.GET.get('format') == 'fragment':
            try:
                return HttpResponse(simplejson.dumps({
                        'redirect': tidy_query_string(request.build_absolute_uri())
                    }), mimetype="application/json")
            except:
                pass
        
        return technical_500_response(request, *exc_info)

    # This will make things prettier if we can manage it.
    # No worries if we can't.
    try:
        from molly.wurfl.context_processors import device_specific_media
        context.update(device_specific_media(request))
    except:
        pass
    
    # This will make stop mixed content warnings if we can manage it
    try:
        from molly.utils.context_processors import ssl_media
        context.update(ssl_media(request))
    except:
        context.update({'STATIC_URL': settings.STATIC_URL})

    response = render_to_response('500.html', context)
    response.status_code = 500
    return response

class CSRFFailureView(BaseView):
    
    def handle_GET(self, request, context, reason=''):
        logger.info('CSRF validation failure: %s', reason)
        return self.render(request, context, 'csrf_failure')
    
    def handle_POST(self, request, context, reason=''):
        return self.handle_GET(request, context, reason)
