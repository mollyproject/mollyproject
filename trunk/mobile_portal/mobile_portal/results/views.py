# Create your views here.
import urllib, re, email.utils, time, datetime
from xml.etree import ElementTree as ET

from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.handlers import BaseView

from mobile_portal.core.breadcrumbs import Breadcrumb, BreadcrumbFactory, lazy_reverse, lazy_parent


class IndexView(BaseView):
    RSS_FEED = 'http://twitter.com/statuses/user_timeline/46711686.rss'
    RESULT_RE = re.compile(r"(?P<code>[A-Z]+) \((?P<title>.+)\)")
    
    def get_metadata(cls, request):
        return {
            'title': 'Results releases',
            'additional': 'View recently released Schools results'
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb('results', None, 'Results releases',
                          lazy_reverse('results_index'))

    def handle_GET(cls, request, context):
        try:
            xml = ET.fromstring(urllib.urlopen(IndexView.RSS_FEED).read())
            x_items = xml.findall('.//item')
            items = []
            for x_item in x_items:
                match = IndexView.RESULT_RE.search(x_item.find('title').text)
                f = x_item.find('title').text
                items.append({
                    'pubDate': datetime.date.fromtimestamp(email.utils.mktime_tz(email.utils.parsedate_tz(x_item.find('pubDate').text))),
                    'code': match.groups()[0],
                    'title': match.groups()[1],
                })
        except:
            items = []
            
        context['items'] = items
        return mobile_render(request, context, 'results/index')
