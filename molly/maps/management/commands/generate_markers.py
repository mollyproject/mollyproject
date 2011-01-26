import itertools, subprocess, os.path, tempfile, os
from django.core.management.base import NoArgsCommand
from django.conf import settings

from molly.maps.osm import MARKER_COLORS, MARKER_RANGE
from molly.maps.osm.models import get_marker_dir

    
class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        template = open(os.path.join(os.path.dirname(__file__), 'markers', 'base.svg')).read()
        marker_dir = get_marker_dir()
        
        if not os.path.exists(marker_dir):
            os.makedirs(marker_dir)
        

        for color, index in itertools.product(MARKER_COLORS, MARKER_RANGE):
            out = template % {
                'label': str(index),
                'fill': color[1],
                'stroke': color[2],
                'text_color': color[3],
            }
            
            f, infile = tempfile.mkstemp()
            os.write(f, out)
            os.close(f)
            
            filename = os.path.join(marker_dir, '%s-%d.png' % (color[0], index))
            subprocess.call(['convert', '-background', 'none', infile, filename])
            os.unlink(infile)
        
        template = open(os.path.join(os.path.dirname(__file__), 'markers', 'star-base.svg')).read()
            
        for color in MARKER_COLORS:
            out = template % {'fill': color[1], 'stroke': color[2]}
            
            f, infile = tempfile.mkstemp()
            os.write(f, out)
            os.close(f)
            
            filename = os.path.join(marker_dir, '%s-star.png' % color[0])
            subprocess.call(['convert', '-background', 'none', infile, filename])
            os.unlink(infile)
