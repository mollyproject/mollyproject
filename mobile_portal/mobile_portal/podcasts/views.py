# Create your views here.
import urllib
from xml.etree import ElementTree as ET
from django.shortcuts import get_object_or_404
from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.models import Feed
from mobile_portal.podcasts.models import Podcast, PodcastCategory
from mobile_portal.podcasts import TOP_DOWNLOADS_RSS_URL

OPML_FEED = 'http://rss.oucs.ox.ac.uk/oxitems/podcastingnewsfeeds.opml'

def index(request):

    context = {
        'categories': PodcastCategory.objects.all(),
    }    
    
    return mobile_render(request, context, 'podcasts/index')

def category_detail(request, code, medium=None):
    category = get_object_or_404(PodcastCategory, code=code)
    podcasts = Podcast.objects.filter(category=category)
    if medium:
        podcasts = podcasts.filter(medium=medium)

    context = {
        'category': category,
        'podcasts': podcasts,
        'medium': medium,
    }
    return mobile_render(request, context, 'podcasts/category_detail')

def podcast_detail(request, code=None, id=None, podcast=None):
    if not podcast:
        podcast = get_object_or_404(Podcast, category__code=code, id=id)
    
    items = podcast.podcastitem_set.order_by('order','-published_date')
    
    context = {
        'podcast': podcast,
        'items': items,
    }
    
    return mobile_render(request, context, 'podcasts/podcast_detail')

def top_downloads(request):
    return podcast_detail(
        request,
        podcast=Podcast.objects.get(rss_url=TOP_DOWNLOADS_RSS_URL)
    )

