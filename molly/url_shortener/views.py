import random
import re
from datetime import timedelta

from django.http import Http404
from django.core.urlresolvers import resolve, reverse
from django.shortcuts import get_object_or_404

from molly.utils.views import BaseView

from models import ShortenedURL

class IndexView(BaseView):
    # We'll omit characters that look similar to one another
    AVAILABLE_CHARS = '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghkmnpqrstuvwxyz'
    has_alpha_re = re.compile(r'[a-zA-Z]')

    def initial_context(self, request):
        try:
            path = request.GET['path']
            view, view_args, view_kwargs = resolve(path.split('?')[0])
            if getattr(view, 'simple_shorten_breadcrumb', False):
                view_context = None
            elif isinstance(view, IndexView):
                view_context = None
            else:
                try:
                    view_context = view.initial_context(request, *view_args, **view_kwargs)
                except Exception, e:
                    view_context = None

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

    @staticmethod
    def breadcrumb(request, context):
        view, view_context = context['view'], context['view_context']
        view_args, view_kwargs = context['view_args'], context['view_kwargs']

        if not isinstance(context['view'], BaseView):
            return None

        if view_context:
            breadcrumb = view.breadcrumb(request, view_context, *view_args, **view_kwargs)
            context['page_title'] = breadcrumb[4]
            return (
                breadcrumb[0],
                breadcrumb[1],
                (breadcrumb[4], context['path']),
                breadcrumb[1] == (breadcrumb[4], context['path']),
                'Shorten link',
            )
        else:
            index = (view.conf.title, reverse('%s:index' % view.conf.local_name))
            return (
                view.conf.local_name,
                index,
                (u'Back\u2026', context['path']),
                context['path'] == index[1],
                'Shorten link',
            )

    def handle_GET(self, request, context):
        try:
            path = request.GET['path']
        except (KeyError):
            return self.invalid_path(request, context)

        if IndexView in getattr(context['view'], '__mro__', ()):
            return self.redirect(path, request, 'perm')

        context['shortened_url'], created = ShortenedURL.objects.get_or_create(path=path)

        if created:
            if context['complex_shorten']:
                slug = None
                while not (slug and ShortenedURL.objects.filter(slug=slug).count() == 0 and self.has_alpha_re.search(slug)):
                    slug = ''.join(random.choice(self.AVAILABLE_CHARS) for i in range(5))
            else:
                slug = unicode(context['shortened_url'].id)
            context['shortened_url'].slug = slug
            context['shortened_url'].save()

        context['url'] = request.build_absolute_uri('/' + context['shortened_url'].slug)

        return self.render(request, context, 'url_shortener/index',
                           expires=timedelta(days=365))
