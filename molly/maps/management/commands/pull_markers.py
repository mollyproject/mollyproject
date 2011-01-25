import itertools, subprocess, os.path
from django.core.management.base import BaseCommand
from optparse import make_option
from django.conf import settings

from molly.osm.utils import MARKER_COLORS, MARKER_RANGE

    
class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--location', dest='location', default=None,
            help='Only load the specified number of items, chosen at random.'),
    )
    help = "Pulls markers from a remote location"

    def handle(self, *args, **options):
        location = options['location']

        files = []        
        for color in MARKER_COLORS:
            color = color[0]
            files.append("%s-star.png" % color)
            for i in MARKER_RANGE:
                files.append("%s-%s.png" % (color, i))
        
        for file in files:
            fn = os.path.join(location, file)
            gn = os.path.join(settings.MARKER_DIR, file)
            f, g = open(fn), open(gn, 'w')
            g.write(f.read())
            f.close()
            g.close()