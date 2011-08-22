import itertools
import subprocess
import os.path
import tempfile
import os
from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.conf import settings

from molly.maps.osm import MARKER_COLORS, MARKER_RANGE
from molly.maps.osm.models import get_marker_dir

    
class Command(NoArgsCommand):
    
    option_list = NoArgsCommand.option_list + (
        make_option('--lazy',
            action='store_true',
            dest='lazy',
            default=False,
            help="Only generate makers if they don't already exist"),
        )
    
    def handle_noargs(self, **options):
        template = open(os.path.join(os.path.dirname(__file__), 'markers', 'base.svg')).read()
        marker_dir = get_marker_dir()
        
        if not os.path.exists(marker_dir):
            os.makedirs(marker_dir)
        

        for color, index in itertools.product(MARKER_COLORS, MARKER_RANGE):
            if os.path.exists(os.path.join(marker_dir, '%s_%d.png' % (color[0], index))):
                continue
            
            out = template % {
                'label': str(index),
                'fill': color[1],
                'stroke': color[2],
                'text_color': color[3],
            }
            
            f, infile = tempfile.mkstemp()
            os.write(f, out)
            os.close(f)
            
            filename = os.path.join(marker_dir, '%s_%d.png' % (color[0], index))
            subprocess.check_call('convert -background none "%s" "%s"' % (infile, filename), shell=True)
            os.unlink(infile)
        
        template = open(os.path.join(os.path.dirname(__file__), 'markers', 'star-base.svg')).read()
            
        for color in MARKER_COLORS:
            if os.path.exists(os.path.join(marker_dir, '%s_star.png' % color[0])):
                continue
            
            out = template % {'fill': color[1], 'stroke': color[2]}
            
            f, infile = tempfile.mkstemp()
            os.write(f, out)
            os.close(f)
            
            filename = os.path.join(marker_dir, '%s_star.png' % color[0])
            subprocess.check_call('convert -background none "%s" "%s"' % (infile, filename), shell=True)
            os.unlink(infile)
