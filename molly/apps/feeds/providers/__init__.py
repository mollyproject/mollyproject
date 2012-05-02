from molly.conf.provider import Provider

class BaseFeedsProvider(Provider):
    pass

from rss import RSSFeedsProvider
from ical import ICalFeedsProvider
from talks_cam import TalksCamFeedsProvider
