import simplejson
import urllib2
import feedparser
import logging
from datetime import timedelta

from django.http import Http404, HttpResponse
from django.template import loader, TemplateDoesNotExist, RequestContext
from django.shortcuts import render_to_response
from django.core.cache import cache

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import NullBreadcrumb

logger = logging.getLogger(__name__)

class IndexView(BaseView):

    def get_metadata(self, request):
        return {
            'exclude_from_search': True}

    breadcrumb = NullBreadcrumb

    def initial_context(self, request):
        return {
            'blog_feed': self._cache(self._get_blog_feed, 'blog',
                                        args=[getattr(self.conf,
                                        'blog_rss_url')], timeout=300),
            'blog_url': getattr(self.conf, 'blog_url', None),
            'facebook_url': getattr(self.conf, 'facebook_url', None),
            'twitter_username': getattr(self.conf, 'twitter_username', None),
            'twitter_widget_id': getattr(self.conf, 'twitter_widget_id', None),
        }

    def handle_GET(self, request, context):
        # Can't render fragment
        if 'fragment' in self.FORMATS: del self.FORMATS['fragment']
        return self.render(request, context, 'desktop/index',
                           expires=timedelta(days=1))

    def _cache(self, f, key, args=None, kwargs=None, timeout=None):
        key = '.'.join(['molly', self.conf.local_name, key])
        value = cache.get(key)
        if value is None:
            value = f(*(args or ()), **(kwargs or {}))
            cache.set(key, value, timeout)
        return value

    def _get_blog_feed(self, url):
        if not url:
            return None

        try:
            return feedparser.parse(url)
        except Exception, e:
            logger.warn("Failed to fetch blog feed.", exc_info=True)
            return None
