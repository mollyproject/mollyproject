from django.core.management.base import BaseCommand
from optparse import make_option
from xml.etree import ElementTree as ET
from datetime import datetime
import urllib, re, email, random
from mobile_portal.podcasts.models import Podcast, PodcastItem, PodcastCategory, PodcastEnclosure
from mobile_portal.podcasts import TOP_DOWNLOADS_RSS_URL

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--maxitems', dest='maxitems', default=None,
            help='Only load the specified number of items, chosen at random.'),
    )
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
#       ('itunesu_code', '{itunesu:}code'),
    )

    CATEGORY_ORDERS = {}

    CATEGORY_RE = re.compile('/([^\/]+)/([^,]+)')
    @staticmethod
    def decode_category(category):
        category = dict(Command.CATEGORY_RE.match(s).groups() for s in category.split(','))
        code, name = category['division_code'], category['division_name']
        name = urllib.unquote(name.replace('+', ' '))

        podcast_category, created = PodcastCategory.objects.get_or_create(code=code,name=name)

        try:
            podcast_category.order = Command.CATEGORY_ORDERS[code]
        except KeyError:
            Command.CATEGORY_ORDERS[code] = len(Command.CATEGORY_ORDERS)
            podcast_category.order = Command.CATEGORY_ORDERS[code]

        podcast_category.save()
        return podcast_category

    RSS_RE = re.compile('http://rss.oucs.ox.ac.uk/(.+-(.+?))/rss20.xml')

    @staticmethod
    def update_from_opml(opml_url, maxitems):

        xml = ET.parse(urllib.urlopen(opml_url))

        rss_urls = [TOP_DOWNLOADS_RSS_URL]

        podcast_elems = xml.findall('.//body/outline')
        if maxitems:
            podcast_elems = random.sample(podcast_elems, maxitems)

        for outline in podcast_elems:
            attrib = outline.attrib
            podcast, created = Podcast.objects.get_or_create(rss_url=attrib['xmlUrl'])

            podcast.category = Command.decode_category(attrib['category'])

            # There are four podcast feed relics that existed before the
            # -audio / -video convention was enforced. These need to be
            # hard-coded as being audio feeds.
            match_groups = Command.RSS_RE.match(attrib['xmlUrl']).groups()
            podcast.medium = {
                'engfac/podcasts-medieval': 'audio',
                'oucs/ww1-podcasts': 'audio',
                'philfac/uehiro-podcasts': 'audio',
                'offices/undergrad-podcasts': 'audio',
            }.get(match_groups[0], match_groups[1])

            rss_urls.append(attrib['xmlUrl'])

            Command.update_podcast(podcast)
            podcast.save()

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
            for attr, x_attr in Command.PODCAST_ATTRS:
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
                podcast_item.podcast_enclosure_set.all().delete()
                podcast_item.delete()

        podcast.most_recent_item_date = max(i.published_date for i in PodcastItem.objects.filter(podcast=podcast))

    @staticmethod
    def update_topdownloads():
        podcast, created = Podcast.objects.get_or_create(rss_url=TOP_DOWNLOADS_RSS_URL)
        podcast.medium = 'audio'
        Command.update_podcast(podcast)
        podcast.save()

    def handle(self, *args, **options):
        maxitems = options['maxitems'] and int(options['maxitems']) or None
        Command.update_from_opml(Command.OPML_FEED, maxitems)
        Command.update_topdownloads()
