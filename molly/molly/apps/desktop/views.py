import simplejson, urllib2, feedparser

from django.http import Http404, HttpResponse
from django.template import loader, TemplateDoesNotExist, RequestContext
from django.shortcuts import render_to_response
from django.core.cache import cache

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import NullBreadcrumb

from molly.apps.home.models import BlogArticle

class IndexView(BaseView):
    def get_metadata(cls, request, page):
        return {
            'exclude_from_search': True
        }

    breadcrumb = NullBreadcrumb
    
    def initial_context(cls, request, page):
        return {
            'twitter_feed': cls._cache(cls._get_twitter_feed, 'twitter', args=[getattr(cls.conf, 'twitter_username')], timeout=300),
            'blog_feed': cls._cache(cls._get_blog_feed, 'blog', args=[getattr(cls.conf, 'blog_rss_url')], timeout=300),
            'twitter_username': getattr(cls.conf, 'twitter_username'),
            'twitter_url': ('http://twitter.com/' + cls.conf.twitter_username) if getattr(cls.conf, 'twitter_username') else None,
        }

    def handle_GET(cls, request, context, page):
        page = page or 'about'
        
        try:
            if page in ('base', 'container'):
                raise TemplateDoesNotExist
            template = loader.get_template('desktop/%s.html' % page)
        except TemplateDoesNotExist, e:
            raise Http404

        content = template.render(RequestContext(request, context))

        if request.GET.get('ajax') == 'true':
            return HttpResponse(content)
        else:
            return render_to_response('desktop/container.html', {
                'content': content,
                'page': page,
            }, context_instance=RequestContext(request))

    def _cache(cls, f, key, args=None, kwargs=None, timeout=None):
        key = '.'.join(['molly', cls.conf.local_name, key])
        value = cache.get(key)
        if value is None:
            print "Fetching"
            value = f(*(args or ()), **(kwargs or {}))
            cache.set(key, value, timeout)
        return value

    _TWITTER_URL = 'http://api.twitter.com/1/statuses/user_timeline.json?user=%s&include_entities=true'
    def _get_twitter_feed(cls, username):
        if not username:
            return None
        
        url = cls._TWITTER_URL % username
        feed = simplejson.load(urllib2.urlopen(url))
        
        if hasattr(cls.conf, 'twitter_ignore_urls'):
            feed = [tweet for tweet in feed if not any(url['url'].startswith(cls.conf.twitter_ignore_urls) for url in tweet['entities']['urls'])]

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