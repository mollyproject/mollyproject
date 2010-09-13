import simplejson, urllib2, feedparser

from django.http import Http404, HttpResponse
from django.template import loader, TemplateDoesNotExist, RequestContext
from django.shortcuts import render_to_response

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import NullBreadcrumb

from molly.apps.home.models import BlogArticle

class IndexView(BaseView):
    def get_metadata(cls, request, page):
        return {
            'exclude_from_search': True
        }

    breadcrumb = NullBreadcrumb
    
    def initial_context(cls, request):
        return {
            'twitter_feed': cls._get_twitter_feed(getattr(cls.conf, 'twitter_username')),
            'blog_feed': cls._get_blog_feed(getattr(cls.conf, 'blog_rss_url')),
            'twitter_username': getattr(cls.conf, 'twitter_username'),
            'twitter_url': ('http://twitter.com/' + cls.conf.twitter_username) if getattr(cls.conf, 'twitter_username') else None,
        }

    def handle_GET(cls, request, context):
        return cls.render(request, context, 'desktop/index')

    _TWITTER_URL = 'http://api.twitter.com/1/statuses/user_timeline.json?user=%s&include_entities=true'
    def _get_twitter_feed(cls, username):
        if not username:
            return None
        
        url = cls._TWITTER_URL % username
        feed = simplejson.load(urllib2.urlopen(url))
        
        if hasattr(cls.conf, 'twitter_ignore_urls'):
            feed = [tweet for tweet in feed if 'entities' in tweet and not any(url['url'].startswith(cls.conf.twitter_ignore_urls) for url in tweet['entities']['urls'])]

        for tweet in feed:
            entities = tweet['entities']
            tweet['formatted_text'] = cls._format_tweet(tweet['text'], entities['urls'], entities['hashtags'], entities['user_mentions'])
        
        return feed
    
    def _format_tweet(cls, text, urls, hashtags, user_mentions):
        text = cls._replace_entities(text, urls, '<a href="%(url)s">%(original)s</a>')
        text = cls._replace_entities(text, hashtags, '<a href="http://search.twitter.com/search?q=%%23%(text)s">%(original)s</a>')
        text = cls._replace_entities(text, user_mentions, '<a href="http://twitter.com/%(screen_name)s" title="%(name)s">%(original)s</a>')
        return text
    
    def _replace_entities(cls, text, entities, replace):
        for entity in reversed(entities):
            start, end = entity['indices']
            entity['original'] = text[start:end]
            text = text[:start] + (replace % entity) + text[end:]
        return text

    def _get_blog_feed(cls, url):
        if not url:
            return None
        
        return feedparser.parse(url)