from xml.etree import ElementTree as ET
from datetime import datetime
import email

from mobile_portal.core.models import feed_fetched
from models import Podcast, PodcastItem, PodcastEnclosure

def process_opml(sender, **kwargs):
    if kwargs.get('category') != 'podcast_opml':
        return
        
    data = sender.get_data()
    
    xml = ET.fromstring(data)
    rss_urls = []
    for outline in xml.findall('.//body/outline'):
        attrib = outline.attrib
        try:
            podcast = Podcast.objects.get(rss_url=attrib['xmlUrl'])
            if podcast.title != attrib['title'] or podcast.description != attrib['description']:
                podcast.title = attrib['title']
                podcast.description = attrib['description']
                podcast.save()
        except Podcast.DoesNotExist:
            podcast = Podcast(
                rss_url = attrib['xmlUrl'],
                title = attrib['title'],
                description = attrib['description'],
            )
            podcast.save()
        rss_urls.append(attrib['xmlUrl'])
    
    for podcast in Podcast.objects.all():
        if not podcast.rss_url in rss_urls:
            podcast.delete()

feed_fetched.connect(process_opml)

PODCAST_ATTRS = (
    ('guid', 'guid'),
    ('title', 'title'),
    ('author', '{itunes:}author'),
    ('duration', '{itunes:}duration'),
    ('published_date', 'pubDate'),
    ('description', 'description'),
)

def process_podcast(sender, **kwargs):
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
        
    if kwargs.get('category') != 'podcast_rss':
        return
        
    podcast = Podcast.objects.get(rss_url=kwargs['url'])
    
    data = sender.get_data()
    xml = ET.fromstring(data)

    guids = []
    for item in xml.findall('.//channel/item'):

        try:
            podcast_item = PodcastItem.objects.get(podcast=podcast, guid=gct(item, 'guid'))
        except PodcastItem.DoesNotExist:
            podcast_item = PodcastItem(podcast=podcast)
        require_save = False
        for attr, x_attr in PODCAST_ATTRS:
            if getattr(podcast_item, attr) != gct(item, x_attr):
                setattr(podcast_item, attr, gct(item, x_attr))
                require_save = True
        if require_save:
            podcast_item.save()

        enc_urls = []            
        for enc in item.findall('enclosure'):
            attrib = enc.attrib
            try:
                podcast_enc = item.podcast_enclosure_set.get(url=attrib['url'])
                if podcast_enc.length != attrib['length'] or podcast_enc.mimetype != attrib['type']:
                    podcast_enc.length = attrib['length']
                    podcast_enc.mimetype = attrib['type']
                    podcast_enc.save()
            except:
                podcast_enc = PodcastEnclosure(
                    podcast_item = podcast_item,
                    url = attrib['url'],
                    length = attrib['length'],
                    mimetype = attrib['type'],
                )
                podcast_enc.save()
            enc_urls.append(attrib['url'])
            
        encs = PodcastEnclosure.objects.filter(podcast_item = podcast_item)
        for enc in encs:
            if not enc.url in enc_urls:
                enc.delete()
        
        guids.append( gct(item, 'guid') )
    
    for podcast_item in PodcastItem.objects.filter(podcast=podcast):
        if not podcast_item.guid in guids:
            podcast_item.podcast_enclosure_set.all().delete()
            podcast_item.delete()
            
feed_fetched.connect(process_podcast)

