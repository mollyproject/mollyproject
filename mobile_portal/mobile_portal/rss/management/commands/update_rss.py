from django.core.management.base import NoArgsCommand

from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
import urllib, re, email, feedparser
from mobile_portal.rss.models import RSSItem, RSSFeed
from mobile_portal.rss.utils import sanitise_html

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads RSS data"

    requires_model_validation = True
    
    def handle_noargs(self, **options):
        for feed in RSSFeed.objects.all():
        
            feed_data = feedparser.parse(feed.rss_url)
            items = list(feed.rssitem_set.all())
            guids = set()
            
            for x_item in feed_data.entries:
                guid, last_modified = x_item.id, datetime(*x_item.date_parsed[:7])
                
                for i in items:
                    if i.guid == guid:
                        item = i
                        break
                else:
                    item = RSSItem(guid=guid, last_modified=datetime(1900,1,1), feed=feed)
                    
                if True or item.last_modified < last_modified:
                    item.title = x_item.title
                    item.description = sanitise_html(x_item.description)
                    item.link = x_item.link
                    item.last_modified = last_modified
                    item.save()
                
                guids.add(guid)
            
            for item in items:
            
                if not item.guid in guids:
                    item.delete()
