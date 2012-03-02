from datetime import datetime
from lxml import etree
import urllib2
import random
import traceback
import logging
import socket
socket.setdefaulttimeout(5)

from molly.external_media import sanitise_html
from molly.conf.settings import batch

from molly.apps.feeds.providers import BaseFeedsProvider

__all__ = ['TalksCamFeedsProvider']

logger = logging.getLogger(__name__)


class TalksCamFeedsProvider(BaseFeedsProvider):
    verbose_name = 'TalksCam'

    @batch('%d * * * *' % random.randint(0, 59))
    def import_data(self, metadata, output):
        """
        Pulls TalksCam feeds
        """

        from molly.apps.feeds.models import Feed
        for feed in Feed.objects.filter(provider=self.class_path):
            output.write("Importing %s\n" % feed.title)
            try:
                self.import_feed(feed)
            except Exception, e:
                output.write("Error importing %s\n" % feed.title)
                traceback.print_exc(file=output)
                output.write('\n')
                logger.warn("Error importing feed %r" % feed.title,
                            exc_info=True, extra={'url': feed.rss_url})

        return metadata

    def import_feed(self, feed):
        from molly.apps.feeds.models import Item, vCard

        xml = etree.parse(urllib2.urlopen(feed.rss_url))

        feed.last_modified = datetime.now()
        feed.save()

        items = set()
        for talk in xml.findall('talk'):
            item, created = Item.objects.get_or_create(feed=feed, guid=talk.find('id').text)

            item.last_modified = self.parse_date(talk.find('updated_at').text)
            item.title = talk.find('title').text.strip()
            item.description = sanitise_html(talk.find('abstract').text.strip())
            item.link = talk.find('url').text
            item.dt_start = self.parse_date(talk.find('start_time').text)
            item.dt_end = self.parse_date(talk.find('end_time').text)
            
            location, created = vCard.objects.get_or_create(name=talk.find('venue').text.strip())
            location.save()
            item.venue = location
            
            item.save()

            items.add(item)

        for item in Item.objects.filter(feed=feed):
            if item not in items:
                item.delete()

        return items

    def parse_date(self, date):
        """
        Parse date as Tue, 21 Feb 2012 23:49:34 +0000
        """
        return datetime.strptime(date[:-6], "%a, %d %b %Y %H:%M:%S")
