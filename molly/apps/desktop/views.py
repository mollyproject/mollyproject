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
            'twitter_feed': self._cache(self._get_twitter_feed, 'twitter',
                                        args=[getattr(self.conf,
                                        'twitter_username')], timeout=300),
            'blog_feed': self._cache(self._get_blog_feed, 'blog',
                                        args=[getattr(self.conf,
                                        'blog_rss_url')], timeout=300),
            'blog_url': getattr(self.conf, 'blog_url', None),
            'facebook_url': getattr(self.conf, 'facebook_url', None),
            'twitter_username': getattr(self.conf, 'twitter_username', None),
            'twitter_url': ('http://twitter.com/' +
                            self.conf.twitter_username)
                            if getattr(self.conf, 'twitter_username', None)
                            else None,
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

    _TWITTER_URL = 'http://api.twitter.com/1/statuses/user_timeline.json?' \
                   + 'screen_name=%s&include_entities=true'

    def _get_twitter_feed(self, username):
        if not username:
            return None

        try:
            url = self._TWITTER_URL % username
            feed = simplejson.load(urllib2.urlopen(url))
        except Exception:
            logger.warn("Failed to fetch Twitter feed.", exc_info=True)
            return None

        if hasattr(self.conf, 'twitter_ignore_urls'):
            """" TODO Rewrite the following list comprehension in nested loops.
             - 10 January 2011 """
            feed = [tweet for tweet in feed if 'entities' in tweet and not
                    any(url['url'].startswith(self.conf.twitter_ignore_urls)
                    for url in tweet['entities']['urls'])]

        for tweet in feed:
            entities = tweet['entities']
            tweet['formatted_text'] = self._format_tweet(tweet['text'],
                                      entities['urls'],
                                      entities['hashtags'],
                                      entities['user_mentions'])

        return feed

    def _format_tweet(self, text, urls, hashtags, user_mentions):
        text = self._replace_entities(text, urls,
            '<a href="%(url)s">%(original)s</a>')
        text = self._replace_entities(text, hashtags,
            '<a href="http://search.twitter.com/search?q=%%23%(text)s">' \
            + '%(original)s</a>')
        text = self._replace_entities(text, user_mentions,
            '<a href="http://twitter.com/%(screen_name)s" title="%(name)s">' \
            + '%(original)s</a>')
        return text

    def _replace_entities(self, text, entities, replace):
        for entity in reversed(entities):
            start, end = entity['indices']
            entity['original'] = text[start:end]
            text = text[:start] + (replace % entity) + text[end:]
        return text

    def _get_blog_feed(self, url):
        if not url:
            return None

        try:
            return feedparser.parse(url)
        except Exception, e:
            logger.warn("Failed to fetch blog feed.", exc_info=True)
            return None
