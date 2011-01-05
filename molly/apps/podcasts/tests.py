import unittest

from django.core.management import call_command
from django.test.client import Client

from molly.apps.podcasts import TOP_DOWNLOADS_RSS_URL
from molly.apps.podcasts.models import Podcast, PodcastCategory
from molly.providers.apps.podcasts.rss import RSSPodcastsProvider
from molly.providers.apps.podcasts.opml import OPMLPodcastsProvider

class PodcastsTestCase(unittest.TestCase):
    def setUp(self):
        if not Podcast.objects.count():
            rss = RSSPodcastsProvider([('top-downloads', 'http://rss.oucs.ox.ac.uk/oxitems/topdownloads.xml')])
            rss.class_path = 'molly.providers.apps.podcasts.rss.RSSPodcastsProvider'
            rss.import_data(None, None)
            opml = OPMLPodcastsProvider('http://rss.oucs.ox.ac.uk/metafeeds/podcastingnewsfeeds.opml')
            opml.class_path = 'molly.providers.apps.podcasts.opml.OPMLPodcastsProvider'
            opml.import_data(None, None)
        
    def testTopDownloads(self):
        c = Client()
        r = c.get('/podcasts/top-downloads/')
        print r.context
        self.assertTrue(r.context['podcast'].podcastitem_set.count() > 0)
        
    def testPodcasts(self):
        podcasts = Podcast.objects.all()
        
        c = Client()
        for podcast in podcasts:
            # Ignore the top downloads podcast
            if podcast.rss_url == TOP_DOWNLOADS_RSS_URL:
                continue
            
            r = c.get('/podcasts/%s/' % podcast.category.slug)
            r = c.get('/podcasts/%s/%d/' % (podcast.category.slug, podcast.id))
            self.assertTrue(r.context['podcast'].podcastitem_set.count() > 0)
            
    def testTidy(self):
        return

        # This isn't going to work as the tidy bindings aren't 64-bit safe,
        # leading to segfaults when dealing with unicode strings. Leaving
        # them as str objects causes failures when dealing with non-ASCII
        # characters in podcasts.
        
        urls = [
            '/podcasts/',
            '/podcasts/top-downloads/',
        ]
        for category in PodcastCategory.objects.all():
            urls.append('podcasts/%s/' % category.code)
            for podcast in category.podcast_set.all():
                urls.append(podcast.get_absolute_url())
                
        c = Client()
        for url in urls:
            response = c.get(url)
            print type(response.content.decode)
            report = tidy.parseString(response.content.decode('utf-8'))
            errors = report.get_errors()
            if len(errors) > 0:
                self.fail("'%s' failed tidy validation: %s" % (url, errors[0]))
            
        
