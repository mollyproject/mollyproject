from django.core.management.base import NoArgsCommand

from xml.etree import ElementTree as ET
from datetime import datetime
import urllib, re, email
from mobile_portal.podcasts.models import Podcast, PodcastItem, PodcastCategory, PodcastEnclosure

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads podcast data"

    requires_model_validation = True
    
    OPML_FEED = 'http://rss.oucs.ox.ac.uk/oxitems/podcastingnewsfeeds.opml'
    
    PODCAST_ATTRS = (
        ('guid', 'guid'),
        ('title', 'title'),
        ('author', '{itunes:}author'),
        ('duration', '{itunes:}duration'),
        ('published_date', 'pubDate'),
        ('description', 'description'),
    )
    
    CATEGORY_RE = re.compile('/division_code/([^,]+),/division_name/(.+)')
    @staticmethod
    def decode_category(category):
        match = Command.CATEGORY_RE.match(category)
        code, name = match.groups()
        name = urllib.unquote(name.replace('+', ' '))
        
        podcast_category, created = PodcastCategory.objects.get_or_create(code=code,name=name)
        return podcast_category



    @staticmethod
    def update_from_opml(opml_url):
        
        xml = ET.parse(urllib.urlopen(opml_url))
        
        rss_urls = []
        for outline in xml.findall('.//body/outline'):
            attrib = outline.attrib
            podcast, created = Podcast.objects.get_or_create(rss_url=attrib['xmlUrl'])

            podcast.title = attrib['title']
            podcast.category = Command.decode_category(attrib['category'])
            podcast.description = attrib['description']
            
            Command.update_podcast(podcast)
            podcast.save()
            
            rss_urls.append(attrib['xmlUrl'])
        
        for podcast in Podcast.objects.all():
            if not podcast.rss_url in rss_urls:
                podcast.delete()

    @staticmethod
    def update_podcast(podcast):
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
    
        guids = []
        for item in xml.findall('.//channel/item'):
    
            podcast_item, created = PodcastItem.objects.get_or_create(podcast=podcast, guid=gct(item, 'guid'))

            require_save = False
            for attr, x_attr in Command.PODCAST_ATTRS:
                if getattr(podcast_item, attr) != gct(item, x_attr):
                    setattr(podcast_item, attr, gct(item, x_attr))
                    require_save = True
            if require_save:
                podcast_item.save()
    
            enc_urls = []            
            for enc in item.findall('enclosure'):
                attrib = enc.attrib
                print item, attrib['url']
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
                podcast_item.podcast_enclosure_set.all().delete()
                podcast_item.delete()
                
        podcast.most_recent_item_date = max(i.published_date for i in PodcastItem.objects.filter(podcast=podcast))
    
    def handle_noargs(self, **options):
        Command.update_from_opml(Command.OPML_FEED)