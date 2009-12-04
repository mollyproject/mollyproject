from django.core.management.base import NoArgsCommand
from django.contrib.gis.geos import Point
from datetime import datetime, timedelta
from xml.utils import iso8601
import ElementSoup as ES
import urllib, re, email, feedparser
from mobile_portal.rss.models import RSSItem, RSSFeed
from mobile_portal.rss.utils import sanitise_html
from mobile_portal.oxpoints.daily_info_ids import daily_info_ids
from mobile_portal.oxpoints.models import Entity, EntityType
from mobile_portal.core import geolocation

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads Daily info events data"

    requires_model_validation = True
    
    DAILY_INFO_VENUE_ID_RE = re.compile('http:\/\/www\.dailyinfo\.co\.uk/reviews/venue/(\d+)/')
    GOOGLE_MAPS_LINK_RE = re.compile('http:\/\/maps\.google\.co\.uk/maps\?q=([^&]+)')
    POSTCODE_RE = re.compile('(OX\d\d? \d[A-Z]{2})')
    SUMMARY_RE = re.compile('(<p>.+?</p>)')
    WHITESPACE_RE = re.compile('\W+')
    
    def postcode_to_point(self, postcode):
        geocodings = geolocation.geocode(postcode)
        if len(geocodings):
            location = geocodings[0][1]
            return Point(location[1], location[0], srid=4326)
        else:
            return None
        
    def handle_noargs(self, **options):
        location_data = {}

        for feed in RSSFeed.events.all():
            if not feed.rss_url.startswith('http://www.dailyinfo.co.uk/'):
                continue

            
            feed_data = feedparser.parse(feed.rss_url)
            items = list(feed.rssitem_set.all())
            guids = set()
            
            for x_item in feed_data.entries:
                guid, last_modified = x_item.id, datetime(*x_item.date_parsed[:7])
                
                
                print x_item.items()
                
                for i in items:
                    if i.guid == guid:
                        item = i
                        break
                else:
                    item = RSSItem(guid=guid, last_modified=datetime(1900,1,1), feed=feed)
                    
                if True or item.last_modified < last_modified:
                    item.title = x_item.xcal_summary
                    
                    try:
                        item.description = sanitise_html(Command.SUMMARY_RE.match(x_item.summary).groups(0)[0])
                    except:
                        item.description = sanitise_html(x_item.summary)
                        
                    item.link = x_item.link
                    item.last_modified = last_modified
                    item.dt_start = datetime.fromtimestamp(iso8601.parse(x_item.xcal_dtstart))
                    item.dt_end = datetime.fromtimestamp(iso8601.parse(x_item.xcal_dtend))
                    
                    item.location_url = x_item.xcal_url
                    
                    venue_id = int(Command.DAILY_INFO_VENUE_ID_RE.match(x_item.xcal_url).groups(0)[0])

                    try:
                        item.location_name, item.location_address, item.location_point = location_data[venue_id]
                    except KeyError:
                        try:
                            source, id = daily_info_ids[venue_id]
                            entity_type = iter(EntityType.objects.filter(source=source)).next()
                            entity = Entity.objects.get(**{str(entity_type.id_field): id})
                            item.location_entity = entity
                            item.location_point = entity.location
                            item.location_name = entity.title
                        except (KeyError, Entity.DoesNotExist):
                            venue_et = ES.parse(urllib.urlopen(item.location_url))
                            item.location_name = [e for e in venue_et.findall('.//div') if e.attrib.get('class')=='heading'][0].text.strip()
                            
                            for link in venue_et.findall('.//a'):
                                match = Command.GOOGLE_MAPS_LINK_RE.match(link.attrib.get('href', ''))
                                if match:
                                    item.location_point = self.postcode_to_point(match.groups(0)[0])
                                    break
                            else:
                                item.location_point = None
                            
                            for para in venue_et.findall('.//p')[1:]:
                                item.location_address = (para.text or '').strip()
                                item.location_address = Command.WHITESPACE_RE.sub(' ', item.location_address)
                                if item.location_point:
                                    break
                                    
                                match = Command.POSTCODE_RE.search(item.location_address)
                                if not match:
                                    break
                                    
                                item.location_point = self.postcode_to_point(match.groups(0)[0])
                                break
                            
                            location_data[venue_id] = item.location_name, item.location_address, item.location_point
                    
                    
                    item.save()

                
                guids.add(guid)
                
            for item in items:
            
                if not item.guid in guids:
                    item.delete()


