from xml.etree import ElementTree as ET
from datetime import datetime
import urllib, re, email, random, logging

from molly.conf.settings import batch
from molly.apps.podcasts.providers import BasePodcastsProvider
from molly.apps.podcasts.models import Podcast, PodcastItem, PodcastCategory, PodcastEnclosure

from molly.apps.podcasts.providers.rss import RSSPodcastsProvider

logger = logging.getLogger(__name__)

class OPMLPodcastsProvider(RSSPodcastsProvider):
    def __init__(self, url, rss_re):
        self.url = url
        self.medium = None
        self.rss_re = re.compile(rss_re)

    CATEGORY_ORDERS = {}

    CATEGORY_RE = re.compile('/([^\/]+)/([^,]+)')
    
    def extract_medium(self, url):
        return 'audio'
    
    def extract_slug(self, xml):
        match_groups = self.rss_re.match(url).groups()
        return match_groups[0]
    
    def decode_category(self, category):
        category = dict(self.CATEGORY_RE.match(s).groups() for s in category.split(','))
        slug, name = category['division_code'], category['division_name']
        name = urllib.unquote(name.replace('+', ' '))

        podcast_category, created = PodcastCategory.objects.get_or_create(slug=slug,name=name)

        try:
            podcast_category.order = self.CATEGORY_ORDERS[slug]
        except KeyError:
            self.CATEGORY_ORDERS[slug] = len(self.CATEGORY_ORDERS)
            podcast_category.order = self.CATEGORY_ORDERS[slug]

        podcast_category.save()
        return podcast_category

    @batch('%d * * * *' % random.randint(0, 59))
    def import_data(self, metadata, output):

        xml = ET.parse(urllib.urlopen(self.url))

        rss_urls = []

        podcast_elems = xml.findall('.//body/outline')

        failure_logged = False

        for outline in podcast_elems:
            attrib = outline.attrib
            if 'xmlUrl' in attrib:
                try:
                    podcast, created = Podcast.objects.get_or_create(
                        provider=self.class_path,
                        rss_url=attrib['xmlUrl'])
                    
                    podcast.medium = self.extract_medium(attrib['xmlUrl'])
                    podcast.category = self.decode_category(attrib['category'])
                    podcast.slug = self.extract_slug(attrib['xmlUrl'])
        
                    rss_urls.append(attrib['xmlUrl'])
        
                    self.update_podcast(podcast)
                except Exception, e:
                    if not failure_logged:
                        logger.exception("Update of podcast %r failed.", attrib['xmlUrl'])
                        failure_logged = True

        for podcast in Podcast.objects.filter(provider=self.class_path):
            if not podcast.rss_url in rss_urls:
                podcast.delete()
        
        return metadata