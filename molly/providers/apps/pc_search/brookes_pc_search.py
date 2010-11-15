from datetime import datetime
import dateutil.parser
import feedparser

class BrookesPCAvailabilityProvider(object):
    def __init__(self, name, slug, url):
        self.name, self.slug, self.url = name, slug, url

    def parse_date(self, s):
        try:
            return dateutil.parser.parse(s)
        except (TypeError, ValueError):
            return None

    def safe_parse(self, f, s):
        try:
            return f(s)
        except (TypeError, ValueError):
            return None

    def get_free_pc(self):
        availability_feed = feedparser.parse(self.url)
       # lastBuildDate = self.parse_date(availability_feed.entries[0].get('ss_lastchecked'))
        
        rooms = []
        for room in availability_feed.entries:
            rooms.append({
                'source': self.slug,
                'source_name': self.name,
                'name': room.get('title'),
				'room_code': room.get('roomcode'),
				'building': room.get('building'),
				'room_no': room.get('room_no'),
				'in_use': room.get(in_use''),
				'total': room.get('total'),
				'campus': room.get('campus'),
				'status': room.get('status'),
				'reserved': room.get('reserved'),
			
           })
	
		return {
            
			'rooms': rooms,
        }


