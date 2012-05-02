from lxml import etree
from datetime import datetime, timedelta
import urllib
import re
import email
import random

from django.conf import settings

from molly.conf.provider import task
from molly.apps.podcasts.providers import BasePodcastsProvider
from molly.apps.podcasts.models import Podcast, PodcastItem, PodcastCategory, PodcastEnclosure
from molly.utils.i18n import set_name_in_language

from rss import RSSPodcastsProvider

class PodcastProducerPodcastsProvider(RSSPodcastsProvider):
    def __init__(self, url):
        self.url = url

    @task(run_every=timedelta(minutes=60))
    def import_data(self, **metadata):
        atom = self.atom
        xml = etree.parse(urllib.urlopen(self.url))

        rss_urls = []

        category_elems = xml.getroot().findall(atom('entry'))
        
        for i, category_elem in enumerate(category_elems):
            link = category_elem.find(atom('link')+"[@rel='alternate']")
            slug = link.attrib['href'].split('/')[-1]
            
            category, created = PodcastCategory.objects.get_or_create(slug=slug)
            set_name_in_language(category, lang_code, name=category_elem.find(atom('title')).text)
            category.order = i
            category.save()
            
            category_xml = etree.parse(urllib.urlopen(link.attrib['href']))
            
            for podcast_elem in category_xml.getroot().findall(atom('entry')):
                url = podcast_elem.find(atom('link')+"[@rel='alternate']").attrib['href']
                slug = url.split('/')[-1]
                podcast, created = Podcast.objects.get_or_create(
                    provider=self.class_path,
                    slug=slug)
                podcast.rss_url = url
        
                podcast.category = category
        
                rss_urls.append(url)
        
                self.update_podcast(podcast)

        for podcast in Podcast.objects.filter(provider=self.class_path):
            if not podcast.rss_url in rss_urls:
                podcast.delete()
        
        return metadata

