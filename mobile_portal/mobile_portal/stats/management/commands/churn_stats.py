from datetime import datetime, timedelta

from django.core.management.base import NoArgsCommand

#import graphication, graphication.linegraph, graphication.scales.date
from graphication import *
from graphication.linegraph import *
from graphication.scales import * 


from mobile_portal.wurfl import device_parents
from mobile_portal.stats.models import Hit

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Generates stats graphs"

    requires_model_validation = True
    
    def handle_noargs(self, **options):
        crawlers = frozenset([
            'crawl', 'spider', 'googlebot',
            'slurp', 'msnbot','zibber',
        ])

        def filter_all(hit):
            return True
        def filter_noncrawler(hit):
            return not any(c in (hit.user_agent or '').lower() for c in crawlers)
        def filter_oxnetwork(hit):
            return (hit.rdns or '').startswith('uk.ac.ox.')
        def filter_iphone(hit):
	        return 'apple_iphone_ver1' in device_parents.get(hit.device_id, ())
        
        filters = {
            'all': filter_all,
            'noncrawler': filter_noncrawler,
            'oxnetwork': filter_oxnetwork,
            'iphone': filter_iphone,
        }
        
        counts = dict((filter, {}) for filter in filters)
        
        an_hour = timedelta(hours=1)
        


        for hit in Hit.objects.filter(requested__gt = datetime.now()-timedelta(14)):
            #exclude James!
            if hit.rdns == 'uk.ac.ox.oucs.slippery-rubber-feet':
                continue

            # Removes some granularity of hit entries (down to hour intervals)
            requested = hit.requested.replace(minute=0, second=0, microsecond=0)
            
            for filter in filters:
                if filters[filter](hit):
                
                    try:
                        counts[filter][requested] += 1
                    except KeyError:
                        counts[filter][requested] = 1
        
        for filter in filters:
            print filter
            
            count = counts[filter] = counts[filter].items()
            count.sort()
            
            # Adds blank entries for times when there are no hits. 
            i = 1
        
            while i < len(count):
                # here be magic   
                gap = (count[i][0] - count[i-1][0])
                to_add = gap.days * 24 + gap.seconds // 3600 - 1
                
                count[i:i] = [(count[i-1][0]+an_hour*(j+1), 0) for j in range(to_add)]
                i += to_add + 1
                
            count = dict(count)
            series = graphication.Series(
                'Hits',
                count,
                '#369',
            )
            series_set = graphication.SeriesSet()
            series_set.add_series(series)
            
            min_, max_ = min(count), max(count)
            
            scale = graphication.scales.date.DateScale(min_, max_, 3600*24)
            lg = graphication.linegraph.LineGraph(series_set, scale)
            
            output = graphication.FileOutput()
            output.add_item(lg, x=0, y=0, width=2000, height=400)
            output.write("pdf", "/home/timf/graphs/%s.pdf" % filter)
            
            print count
            
