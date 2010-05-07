from django.core.management.base import NoArgsCommand

from datetime import datetime, timedelta
import urllib, re, email, feedparser
from molly.rss.models import Feed
from molly.rss.utils import sanitise_html
from molly.rss.importers import importers

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads RSS data"

    requires_model_validation = True
    
    def handle_noargs(self, **options):
        for feed in Feed.objects.all():
            
            print "Importing %s" % feed.rss_url
            importer = importers[feed.importer]
            item_set = importer.update(feed)
            
            for item in feed.item_set.all():
                if item not in item_set:
                    item.delete()
            
