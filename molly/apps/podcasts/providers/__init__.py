from molly.conf.provider import Provider

class BasePodcastsProvider(Provider):
    pass

from rss import RSSPodcastsProvider
from pp import PodcastProducerPodcastsProvider
from opml import OPMLPodcastsProvider
