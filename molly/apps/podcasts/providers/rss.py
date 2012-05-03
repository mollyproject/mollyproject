import random, urllib, email
from lxml import etree
from datetime import datetime, timedelta

from molly.conf.provider import task
import dateutil.parser

from molly.apps.podcasts.providers import BasePodcastsProvider
from molly.apps.podcasts.models import Podcast, PodcastItem, PodcastEnclosure

class Namespace(object):
    def __init__(self, ns):
        self.ns = ns
    def __call__(self, local):
        return '{%s}%s' % (self.ns, local)

class RSSPodcastsProvider(BasePodcastsProvider):
    @property
    def PODCAST_ATTRS(self):
        atom = self.atom
        return (
            ('guid', ('guid', atom('id'),)),
            ('title', ('title', atom('title'),)),
            ('author', ('{itunes:}author',)),
            ('duration', ('{itunes:}duration',)),
            ('published_date', ('pubDate', atom('published'),)),
            ('description', ('description', atom('summary'),)),
    #       ('itunesu_code', '{itunesu:}code'),
        )

    def __init__(self, podcasts, medium=None):
        self.podcasts = podcasts
        self.medium = medium
    
    @property
    def atom(self):
        return Namespace('http://www.w3.org/2005/Atom')
    
    @task(run_every=timedelta(minutes=60))
    def import_data(self, **metadata):
        for slug, url in self.podcasts:
            podcast, url = Podcast.objects.get_or_create(
                provider=self.class_path,
                rss_url=url,
                defaults={'slug': slug})
            if self.medium: 
                podcast.medium = self.medium
                
            podcast.slug = slug
            self.update_podcast.delay(podcast)
            
    def determine_license(self, o):
        license = o.find('{http://purl.org/dc/terms/}license') or \
                  o.find('{http://backend.userland.com/creativeCommonsRssModule}license')
        
        return getattr(license, 'text', None)
        
    @task()
    def update_podcast(self, podcast):
        atom = self.atom
        def gct(node, names):
            for name in names:
                if node.find(name) is None:
                    continue
                value = node.find(name).text
                if name == 'pubDate':
                    value = datetime.fromtimestamp(
                        email.utils.mktime_tz(
                            email.utils.parsedate_tz(value)))
                elif name == atom('published'):
                    value = dateutil.parser.parse(value)
                elif name == '{itunes:}duration':
                    value = int(value)
                return value
            return None

        xml = etree.parse(urllib.urlopen(podcast.rss_url)).getroot()

        try:
            podcast.title = xml.find('.//channel/title').text
            podcast.description = xml.find('.//channel/description').text
        except AttributeError:
            podcast.title = xml.find(atom('title')).text
            podcast.description = xml.find(atom('subtitle')).text
        
        podcast.license = self.determine_license(xml.find('.//channel'))
        if self.medium is not None:
            podcast.medium = self.medium

        logo = xml.find('.//channel/image/url')
        podcast.logo = logo.text if logo is not None else None

        ids = []
        for item in xml.findall('.//channel/item') or xml.findall(atom('entry')):
            id = gct(item, ('guid', atom('id'),))
            if not id:
                continue
            
            try:
                podcast_item, created = PodcastItem.objects.get_or_create(podcast=podcast, guid=id)
            except PodcastItem.MultipleObjectsReturned:
                PodcastItem.objects.filter(podcast=podcast, guid=id).delete()
                podcast_item, created = PodcastItem.objects.get_or_create(podcast=podcast, guid=id)

            old_order = podcast_item.order
            try:
                podcast_item.order = int(item.find('{http://ns.ox.ac.uk/namespaces/oxitems/TopDownloads}position').text)
            except (AttributeError, TypeError):
                pass

            require_save = old_order != podcast_item.order
            for attr, x_attrs in self.PODCAST_ATTRS:
                if getattr(podcast_item, attr) != gct(item, x_attrs):
                    setattr(podcast_item, attr, gct(item, x_attrs))
                    require_save = True
            license = self.determine_license(item)
            if require_save or podcast_item.license != license:
                podcast_item.license = license
                podcast_item.save()

            enc_urls = []
            for enc in item.findall('enclosure') or item.findall(atom('link')):
                attrib = enc.attrib
                url = attrib.get('url', attrib.get('href'))
                podcast_enc, updated = PodcastEnclosure.objects.get_or_create(podcast_item=podcast_item, url=url)
                try:
                    podcast_enc.length = int(attrib['length']) 
                except ValueError:
                    podcast_enc.length = None
                podcast_enc.mimetype = attrib['type']
                podcast_enc.save()
                enc_urls.append(url)

            encs = PodcastEnclosure.objects.filter(podcast_item = podcast_item)
            for enc in encs:
                if not enc.url in enc_urls:
                    enc.delete()

            ids.append( id )

        for podcast_item in PodcastItem.objects.filter(podcast=podcast):
            if not podcast_item.guid in ids:
                podcast_item.podcastenclosure_set.all().delete()
                podcast_item.delete()

        #podcast.most_recent_item_date = max(i.published_date for i in PodcastItem.objects.filter(podcast=podcast))
        podcast.save()
