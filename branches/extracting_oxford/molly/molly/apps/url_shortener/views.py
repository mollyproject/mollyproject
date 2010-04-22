import random

from django.http import HttpResponsePermanentRedirect, Http404
from django.core.urlresolvers import resolve, reverse
from django.shortcuts import get_object_or_404

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import NullBreadcrumb

from models import ShortenedURL

class IndexView(BaseView):
    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context):
        raise Http404

class ShortenedURLRedirectView(BaseView):
    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context, slug):
        shortened_url = get_object_or_404(ShortenedURL, slug=slug)
        return HttpResponsePermanentRedirect(shortened_url.path)

class ShortenURLView(BaseView):
    # We'll omit characters that look similar to one another
    AVAILABLE_CHARS = '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghkmnpqrstuvwxyz'

    def initial_context(cls, request):
        try:
            path = request.GET['path']
            view, view_args, view_kwargs = resolve(path.split('?')[0])
            if getattr(view, 'simple_shorten_breadcrumb', False):
                view_context = None
            else:
                view_context = view.initial_context(request, *view_args, **view_kwargs)

        except (KeyError, ):
            raise Http404

        return {
            'path': path,
            'view': view,
            'view_args': view_args,
            'view_kwargs': view_kwargs,
            'view_context': view_context,
            'complex_shorten': ('?' in path) or view_context is None or view_context.get('complex_shorten', False),
        }

    def breadcrumb_render(cls, request, context):
        view, view_context = context['view'], context['view_context']
        view_args, view_kwargs = context['view_args'], context['view_kwargs']

        if view_context:
            breadcrumb = view.breadcrumb.render(view, request, view_context, *view_args, **view_kwargs)
            return (
                breadcrumb[0],
                breadcrumb[1],
                (breadcrumb[4], context['path']),
                breadcrumb[1] == (breadcrumb[4], context['path']),
                'Shorten link',
            )
        else:
            index = resolve(reverse('%s_index' % view.app_name))[0].breadcrumb(request, context)
            index = index.title, index.url()
            return (
                view.app_name,
                index,
                (u'Back\u2026', context['path']),
                False,
                'Shorten link',
            )

    # Create a 'blank' object to attach our render method to by constructing
    # a class and then calling its constructor. It's a bit messy, and probably
    # points at a need to refactor breadcrumbs so that view.breadcrumb returns
    # the five-tuple passed to the template as opposed to
    # view.breadcrumb.render. 
    breadcrumb = type('bc', (object,), {})()
    breadcrumb.render = breadcrumb_render


    def handle_GET(cls, request, context):
        print context['complex_shorten']
        try:
            path = request.GET['path']
        except (KeyError):
            return cls.invalid_path(request, context)

        context['shortened_url'], created = ShortenedURL.objects.get_or_create(path=path)

        if created:
            if context['complex_shorten']:
                slug = '0'+''.join(random.choice(cls.AVAILABLE_CHARS) for i in range(5))
            else:
                slug = unicode(context['shortened_url'].id)
            context['shortened_url'].slug = slug
            context['shortened_url'].save()

        return cls.render(request, context, 'core/shorten_url')
