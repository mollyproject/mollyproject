from django.core.management.base import NoArgsCommand
from django.template import loader, Context

from datetime import datetime
import feedparser, time
from molly.core.models import BlogArticle

def struct_to_datetime(s):
    return datetime.fromtimestamp(time.mktime(s))
    
class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Updates blog articles on the desktop site"

    requires_model_validation = True
    
    RSS_URL = 'http://mobileoxford.posterous.com/rss.xml'
    RSS_URL = 'http://feeds.feedburner.com/posterous/yAEj'
    
    def handle_noargs(self, **options):
        feed = feedparser.parse(self.RSS_URL)
        template = loader.get_template('core/exposition/article.xhtml')

        guids = set()        
        for item in feed.entries[:5]:
            article, created = BlogArticle.objects.get_or_create(guid=item.guid, defaults={'updated': datetime.now(), 'html':''})
            
            item['modified_datetime'] = struct_to_datetime(item.modified_parsed)
            article.html = template.render(Context(item))
            article.updated = item.modified_datetime
            
            print item.keys()
            
            article.save()
            guids.add(item.guid)
        
        for article in BlogArticle.objects.all():
            if article.guid not in guids:
                article.delete()
