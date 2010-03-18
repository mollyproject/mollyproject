import itertools, subprocess, os.path
from django.core.management.base import NoArgsCommand
from django.conf import settings

from molly.osm.utils import MARKER_COLORS, MARKER_RANGE

    
class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        template = open(os.path.join(os.path.dirname(__file__), 'base.svg')).read()
        marker_dir = settings.MARKER_DIR
        
        if not os.path.exists(marker_dir):
            os.makedirs(marker_dir)
        

        for color, index in itertools.product(MARKER_COLORS, MARKER_RANGE):
            out = template % {
                'label': str(index),
                'fill': color[1],
                'stroke': color[2],
                'text_color': color[3],
            }
            
            f = open('out.svg', 'w')
            f.write(out)
            f.close()
            
            filename = os.path.join(marker_dir, '%s-%d.png' % (color[0], index))
            subprocess.call([
                'inkscape',
                'out.svg',
                '--export-png=%s' % filename,
            ])
        
        template = open(os.path.join(os.path.dirname(__file__), 'star-base.svg')).read()
            
        for color in MARKER_COLORS:
            out = template % {'fill': color[1], 'stroke': color[2]}
            
            f = open('out.svg', 'w')
            f.write(out)
            f.close()
            
            filename = os.path.join(marker_dir, '%s-star.png' % color[0])
            subprocess.call([
                'inkscape',
                'out.svg',
                '--export-png=%s' % filename,
            ])