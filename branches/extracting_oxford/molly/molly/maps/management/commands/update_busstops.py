
import os.path, re, ftplib
from django.core.management.base import NoArgsCommand

from xml.etree import ElementTree as ET
from django.contrib.gis.geos import Point
from molly.maps.models import Entity, EntityType

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    import credentials
except ImportError:
    raise ImportError("Please create a credentials.py in oxpoints/management/commands")

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads NaPTAN bus stop data."
    
    requires_model_validation = True

    NS = '{http://www.naptan.org.uk/}'
    CENTRAL_STOP_RE = re.compile('Stop ([A-Z]\d)')
    
    @staticmethod
    def atco(c):
        return unicode(min(9, (ord(c)-91)//3))

    def add_busstop_entity_type(self):
        self.entity_type, created = EntityType.objects.get_or_create(slug='busstop')
        self.entity_type.artcile = 'a'
        self.entity_type.verbose_name = 'bus stop'
        self.entity_type.verbose_name_plural = 'bus stops'
        self.entity_type.source = 'naptan'
        self.entity_type.id_field = 'atco_code'
        self.entity_type.show_in_nearby_list = True
        self.entity_type.show_in_category_list = False
        self.entity_type.save()

    def parse_busstops(self):

        def NS(elements):
            return "/".join((Command.NS + e) for e in elements.split('/'))

        self.data.seek(0)
        xml = ET.parse(self.data)
        
        stops, atco_codes = xml.findall('.//'+NS('StopPoint')), set()
        
        for stop in stops:
	
            if stop.attrib['Status'] == 'inactive':
                continue

            atco_code = stop.find(NS('AtcoCode')).text.strip()
            if not stop.find(NS('NaptanCode')) is None:
                naptan_code = stop.find(NS('NaptanCode')).text.strip()
                naptan_code = ''.join(map(Command.atco, naptan_code))
            else:
                naptan_code = None
                
            atco_codes.add (atco_code)

            translation = stop.find(NS('Place/Location/Translation'))
            location = float(translation.find(NS('Latitude')).text), float(translation.find(NS('Longitude')).text)
            
			#Description of stops
            descriptor = stop.find(NS('Descriptor'))
            title = "\n ".join("%s: %s" % (e.tag[len(Command.NS):], e.text) for e in descriptor)
            
            cnm, lmk, ind, str = [(descriptor.find(NS(s)).text if descriptor.find(NS(s)) != None else None) for s in ['CommonName', 'Landmark','Indicator','Street']]
            
            if lmk and ind and ind.endswith(lmk) and len(ind) > len(lmk):
                ind = ind[:-len(lmk)]
                
                
            if ind == 'Corner':
                title = "Corner of %s and %s" % (str, lmk)
            elif cnm == str:
                title = "%s, %s" % (ind, cnm)
            elif ind == lmk:
                title = "%s, %s" % (lmk, str)
            elif lmk != str:
                title = "%s %s, on %s" % (ind, lmk, str)
            else:
                title = "%s %s, %s" % (ind, lmk, cnm)

            entity, created = Entity.objects.get_or_create(atco_code = atco_code, entity_type=self.entity_type)
            entity.all_types.add(entity.entity_type)

            match = ind and Command.CENTRAL_STOP_RE.match(ind)
            if match:
                entity.central_stop_id = match.groups(0)[0]
            
            entity.naptan_code = naptan_code
            entity.location = Point(location[1], location[0], srid=4326)
            entity.geometry = entity.location
            entity.title = title
            entity.save()
    
        for entity in Entity.objects.filter(entity_type=self.entity_type):
            if not entity.atco_code in atco_codes:
                entity.delete()

    def chomp_data(self, block):
        self.data.write(block)
                
    def handle_noargs(self, **options):

        self.add_busstop_entity_type()
        
        ftp = ftplib.FTP('journeyweb.org.uk',
            credentials.user,
            credentials.password,
        )
        ftp.cwd('/V2/340/')
        self.data = StringIO()
        ftp.retrbinary('RETR NaPTAN340.xml', self.chomp_data)
        ftp.quit()
        
        self.parse_busstops()
