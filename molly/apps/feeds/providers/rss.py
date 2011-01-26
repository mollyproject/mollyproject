from datetime import datetime, timedelta
import urllib, re, email, feedparser, time, random, traceback, logging

from molly.external_media import sanitise_html
from molly.conf.settings import batch

from molly.apps.feeds.providers import BaseFeedsProvider

__all__ = ['RSSFeedsProvider']

def parse_date(s):
    return struct_to_datetime(feedparser._parse_date(s))
def struct_to_datetime(s):
    return datetime.fromtimestamp(time.mktime(s))

logger = logging.getLogger('molly.apps.providers.feeds.rss')

class RSSFeedsProvider(BaseFeedsProvider):
    verbose_name = 'RSS'
    
    @batch('%d * * * *' % random.randint(0, 59))
    def import_data(self, metadata, output):
        "Pulls RSS feeds"

        from molly.apps.feeds.models import Feed
        for feed in Feed.objects.filter(provider=self.class_path):
            output.write("Importing %s\n" % feed.title)
            try:
                self.import_feed(feed)
            except Exception, e:
                output.write("Error importing %s\n" % feed.title)
                traceback.print_exc(file=output)
                output.write('\n')
                logger.warn("Error importing feed %r" % feed.title, exc_info=True, extra={'url': feed.rss_url})
            
        return metadata
            
    def import_feed(self, feed):
        from molly.apps.feeds.models import Item
        
        feed_data = feedparser.parse(feed.rss_url)
        try:
            feed.last_modified = struct_to_datetime(feed_data.feed.updated_parsed)
        except:
            feed.last_modified = parse_date(feed_data.headers.get('last-modified', datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")))
            
        feed.save()
        
        items = set()
        for x_item in feed_data.entries:
            guid, last_modified = x_item.id, datetime(*x_item.date_parsed[:7])
            
            for i in items:
                if i.guid == guid:
                    item = i
                    break
            else:
                try:
                    item = Item.objects.get(guid=guid, feed=feed)
                except Item.DoesNotExist:
                    item = Item(guid=guid, last_modified=datetime(1900,1,1), feed=feed)

            if True or item.last_modified < last_modified:
                item.title = x_item.title
                item.description = sanitise_html(x_item.get('description', ''))
                item.link = x_item.link
                item.last_modified = last_modified
                item.save()
            
            items.add(item)
        
        for item in Item.objects.filter(feed=feed):
            if item not in items:
                item.delete()
        
        return items
