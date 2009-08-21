from django.core.management.base import NoArgsCommand

from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
import urllib, re, email
from mobile_portal.rss.models import RSSItem, RSSFeed


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads RSS data"

    requires_model_validation = True
    
    def handle_noargs(self, **options):
        for feed in RSSFeed.objects.all():
            xml = ET.parse(urllib.urlopen(feed.rss_url))
            
            guids = set()
            items = dict((f.guid, f) for f in feed.rssitem_set.all())
            
            for x_item in xml.getroot().findall('channel/item'):
                guid, pub_date = x_item.find('guid').text, x_item.find('pubDate').text
                last_modified = datetime.strptime(pub_date[:25], "%a, %d %b %Y %H:%M:%S")
                last_modified = last_modified - timedelta(hours=int(pub_date[26:29]), minutes=int(pub_date[29:31]))

                if guid in items:
                    item = items[guid]
                else:
                    item = RSSItem(guid=guid, last_modified=datetime(1900,1,1), feed=feed)
                    
                if item.last_modified < last_modified:
                    item.title = x_item.find('title').text
                    item.description = x_item.find('description').text
                    item.link = x_item.find('link').text
                    item.last_modified = last_modified
                    item.save()
                
                guids.add(guid)
            
            for item in items.values():
                if not item.guid in guids:
                    item.delete()
