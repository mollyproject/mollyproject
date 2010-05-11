import random, urllib, email
from xml.etree import ElementTree as ET
from datetime import datetime

from molly.conf.settings import batch

from molly.apps.podcasts.providers import BasePodcastsProvider
from molly.apps.podcasts.models import Podcast, PodcastItem, PodcastEnclosure

class RSSPodcastsProvider(BasePodcastsProvider):
    PODCAST_ATTRS = (
        ('guid', 'guid'),
        ('title', 'title'),
        ('author', '{itunes:}author'),
        ('duration', '{itunes:}duration'),
        ('published_date', 'pubDate'),
        ('description', 'description'),
#       ('itunesu_code', '{itunesu:}code'),
    )

    def __init__(self, podcasts):
        self.podcasts = podcasts
    
    @batch('%d * * * *' % random.randint(0, 59))
    def import_data(self, metadata, output):
        for slug, url in self.podcasts:
            podcast, url = Podcast.objects.get_or_create(
                provider=self.class_path,
                rss_url=url,
                defaults={'slug': slug})
            
            podcast.slug = slug
            self.update_podcast(podcast)
            
        
    def update_podcast(self, podcast):
        def gct(node, name):
            try:
                value = node.find(name).text
                if name == 'pubDate':
                    value = datetime.fromtimestamp(
                        email.utils.mktime_tz(
                            email.utils.parsedate_tz(value)))
                elif name == '{itunes:}duration':
                    value = int(value)
                return value
            except AttributeError:
                return None

        xml = ET.parse(urllib.urlopen(podcast.rss_url))

        podcast.title = xml.find('.//channel/title').text
        podcast.description = xml.find('.//channel/description').text

        guids = []
        for item in xml.findall('.//channel/item'):
            if not gct(item, 'guid'):
                continue

            podcast_item, created = PodcastItem.objects.get_or_create(podcast=podcast, guid=gct(item, 'guid'))

            old_order = podcast_item.order
            try:
                podcast_item.order = int(item.find('{http://ns.ox.ac.uk/namespaces/oxitems/TopDownloads}position').text)
            except (AttributeError, TypeError):
                pass

            require_save = old_order != podcast_item.order
            for attr, x_attr in self.PODCAST_ATTRS:
                if getattr(podcast_item, attr) != gct(item, x_attr):
                    setattr(podcast_item, attr, gct(item, x_attr))
                    require_save = True
            if require_save:
                podcast_item.save()

            enc_urls = []
            for enc in item.findall('enclosure'):
                attrib = enc.attrib
                podcast_enc, updated = PodcastEnclosure.objects.get_or_create(podcast_item=podcast_item, url=attrib['url'])
                try:
                    podcast_enc.length = int(attrib['length'])
                except ValueError:
                    podcast_enc.length = None
                podcast_enc.mimetype = attrib['type']
                podcast_enc.save()
                enc_urls.append(attrib['url'])

            encs = PodcastEnclosure.objects.filter(podcast_item = podcast_item)
            for enc in encs:
                if not enc.url in enc_urls:
                    enc.delete()

            guids.append( gct(item, 'guid') )

        for podcast_item in PodcastItem.objects.filter(podcast=podcast):
            if not podcast_item.guid in guids:
                podcast_item.podcastenclosure_set.all().delete()
                podcast_item.delete()

        podcast.most_recent_item_date = max(i.published_date for i in PodcastItem.objects.filter(podcast=podcast))

        podcast.save()