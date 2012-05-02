import sys
from django.utils import unittest

from django.core.management import call_command
from django.test.client import Client

from molly.apps.podcasts.models import Podcast, PodcastCategory
from molly.apps.podcasts.providers import OPMLPodcastsProvider

class PodcastsTestCase(unittest.TestCase):
    def setUp(self):
        if not Podcast.objects.count():
            opml = OPMLPodcastsProvider(url = 'http://www.bbc.co.uk/radio/opml/bbc_podcast_opml_v2.xml',
                                        rss_re = r'http://downloads.bbc.co.uk/podcasts/(.+)/rss.xml')
            opml.class_path = 'molly.providers.apps.podcasts.opml.OPMLPodcastsProvider'
            opml.import_data({})
        
    def testPodcasts(self):
        podcasts = Podcast.objects.all()
        
        c = Client()
        for podcast in podcasts:
            
            r = c.get('/podcasts/%s/' % podcast.category.slug)
            r = c.get('/podcasts/%s/%s/' % (podcast.category.slug, podcast.slug))
            self.assertTrue(r.context['podcast'].podcastitem_set.count() > 0)
