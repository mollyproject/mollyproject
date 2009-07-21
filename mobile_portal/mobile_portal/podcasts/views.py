# Create your views here.
import urllib
from xml.etree import ElementTree as ET
from django.shortcuts import get_object_or_404
from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.models import Feed
from mobile_portal.podcasts.models import Podcast

OPML_FEED = 'http://rss.oucs.ox.ac.uk/oxitems/podcastingnewsfeeds.opml'
RSS_FEED = 'http://rss.oucs.ox.ac.uk/mpls/oxsci-audio/rss20.xml?destination=poau'
def index(request):
    Feed.fetch(OPML_FEED, category='podcast_opml', fetch_period=3600*24)

    context = {
        'podcasts': Podcast.objects.order_by('title')
    }    
    
    return mobile_render(request, context, 'podcasts/index')

def podcast_detail(request, id):
    podcast = get_object_or_404(Podcast, id=id)
    
    Feed.fetch(podcast.rss_url, category='podcast_rss', fetch_period=3600*24)
    
    items = podcast.podcastitem_set.order_by('-published_date')
    
    context = {
        'podcast': podcast,
        'items': items,
    }
    
    return mobile_render(request, context, 'podcasts/podcast_detail')