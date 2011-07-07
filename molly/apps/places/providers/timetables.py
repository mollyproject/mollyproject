from collections import namedtuple, defaultdict
from datetime import datetime, time
from logging import getLogger
from operator import itemgetter
from django.db.models import Q

from molly.apps.places.providers import BaseMapsProvider

class TimetableAnnotationProvider(BaseMapsProvider):
    """
    This provider adds scheduled transport information to entites
    """
    
    def augment_metadata(self, entities, **kwargs):
        
        # Some routes finish the day after they start on, but for the
        # "does this service run today" question, they consider the day
        # before, e.g., Metrolink saturday timetable finishes early
        # Sunday morning. We're going to assume a break of 4am - but
        # this might not be accurate!
        
        today = datetime.now()
        if today.time() < time(4):
            today -= timedelta(days=1)
        
        def midnight_4am(left, right):
            """
            Search comparison function where before 4 am is later than midnight
            """
            return cmp(left.hour if left.hour >= 4 else left.hour + 24,
                       right.hour if right.hour >= 4 else right.hour + 24)
        
        for entity in entities:
            
            # Skip stops we have no schedules for
            if entity.scheduledstop_set.all().count() == 0:
                continue
            
            services = defaultdict(list)
            for stop in entity.scheduledstop_set.filter(
                Q(sta__gte=today.time()) | Q(sta__lt=time(4))):
                
                if not stop.journey.runs_on(today.date()):
                    continue
                
                services[(stop.journey.route.service_id, stop.journey.route.service_name)].append((stop.journey, stop.std if stop.std else stop.sta))
            
            services = ((route, sorted(ss, key=itemgetter(1), cmp=midnight_4am))
                for route, ss in services.items())
            
            services = [{
                'service': service_id,
                'destination': service_name,
                'next': ss[0][1].strftime('%H:%M'),
                'following': map(lambda t: t[1].strftime('%H:%M'), ss[1:4]),
                'journey': ss[0][0]
            } for (service_id, service_name), ss in sorted(services, key=lambda x: x[1][0][1])]
            
            entity.metadata['real_time_information'] = {
                'services': services,
                'pip_info': [],
            }
            entity.metadata['meta_refresh'] = 60

