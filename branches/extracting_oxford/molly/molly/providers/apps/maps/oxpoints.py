import simplejson, urllib

from django.contrib.gis.geos import Point

from molly.maps.providers import BaseMapsProvider
from molly.maps.models import Entity, EntityType, Source

class OxpointsMapsProvider(BaseMapsProvider):

    ALL_OXPOINTS = 'http://oxpoints.oucs.ox.ac.uk/all.json'

    OXPOINTS_TYPES = {
        'College': ('college',),
        'Department': ('department',),
        'Carpark': ('car-park', 'university-entity'),
        'Room': ('room', 'university-entity'),
        'Library': ('library', 'university-entity'),
        'SubLibrary': ('library-collection', 'university-entity'),
        'Museum': ('museum', 'university-entity'),
        'Building': ('building', 'university-entity'),
        'Unit': ('unit',),
        'Faculty': ('faculty',),
        'Division': ('division',),
        'University': ('university',),
        'Space': ('space', 'university-entity'),
        'WAP': ('wireless-access-point', 'university-entity'),
        'Site': ('site', 'university-entity'),
        'Hall': ('hall',),
    }
    
    def load_entity_types(self):
        """
        Load the entity types into the database, returning a dictionary from
        rdf types (less the namespace) to EntityType objects.
        """

        # Define the types of OxPoints entities we'll be loading
        ENTITY_TYPES = {
            'college':               ('college', 'colleges', False, False, ('college-hall',)),
            'college-hall':          ('college or PPH', 'colleges and PPHs', True, True, ('university-entity',)),
            'university-entity':     ('University entity', 'University entities', False, False, ()),
            'department':            ('department', 'departments', False, False, ('unit',)),
            'car-park':              ('car park', 'car parks', True, True, ()),
            'room':                  ('room', 'rooms', True, False, ('space',)),
            'space':                 ('space', 'spaces', False, False, ()),
            'library':               ('library', 'libraries', True, True, ()),
            'library-collection':    ('library collection', 'library collections', False, False, ()),
            'museum':                ('museum', 'museums', True, True, ()),
            'building':              ('building', 'buildings', True, True, ()),
            'unit':                  ('unit', 'units', True, True, ('university-entity',)),
            'faculty':               ('faculty', 'faculties', False, False, ('unit',)),
            'division':              ('division', 'divisions', False, False, ('unit',)),
            'university':            ('University', 'Universities', False, False, ('university-entity',)),
            'wireless-access-point': ('wireless access point', 'wireless access points', False, False, ()),
            'site':                  ('site', 'site', False, False, ()),
            'hall':                  ('PPH', 'PPHs', False, False, ('college-hall',)),
        }

        entity_types = {}
        new_entity_types = set()
        for slug, (verbose_name, verbose_name_plural, nearby, category, subtype_of) in ENTITY_TYPES.items():
            try:
                entity_type = EntityType.objects.get(slug=slug)
            except EntityType.DoesNotExist:
                entity_type = EntityType(
                    slug = slug,
                    verbose_name = verbose_name,
                    verbose_name_plural = verbose_name_plural,
                    article = 'a',
                    show_in_nearby_list = nearby,
                    show_in_category_list = category,
                )
                entity_type.save()
                new_entity_types.add(slug)
            entity_types[slug] = entity_type
        
        for slug in new_entity_types:
            subtype_of = ENTITY_TYPES[slug][4]
            for s in subtype_of:
                entity_types[slug].subtype_of.add(entity_types[s])
            entity_types[slug].save()
            
        self.entity_types = entity_types

    def _get_source(self):
        try:
            source = Source.objects.get(module_name="molly.providers.apps.maps.oxpoints")
        except Source.DoesNotExist:
            source = Source(module_name="molly.providers.apps.maps.oxpoints")
        
        source.name = "OxPoints"
        source.save()
        
        return source
        
    def import_data(self):
        self.load_entity_types()
        
        data = simplejson.load(urllib.urlopen(self.ALL_OXPOINTS))
        source = self._get_source()
        
        for datum in data:
            oxpoints_id = datum['uri'].rsplit('/')[-1]
            oxpoints_type = datum['type'].rsplit('#')[-1]
            
            if not oxpoints_type in self.OXPOINTS_TYPES:
                continue
                
            try:
                entity = Entity.objects.get(source=source, _identifiers__scheme='oxpoints', _identifiers__value=oxpoints_id)
            except Entity.DoesNotExist:
                entity = Entity(source=source)
                
            entity.title = datum.get('oxp_fullyQualifiedTitle', datum.get('dc_title', ''))
            entity.primary_type = self.entity_types[self.OXPOINTS_TYPES[oxpoints_type][0]]
            
            if 'geo_lat' in datum and 'geo_long' in datum:
                entity.location = Point(datum['geo_long'], datum['geo_lat'], srid=4326)
            else:
                entity.location = None
            
            entity.metadata['oxpoints'] = datum
            
            identifiers = {
                'oxpoints': oxpoints_id,
                'uri': datum['uri'],
            }
            
            entity.save(identifiers=identifiers)
            entity.all_types = [self.entity_types[t] for t in self.OXPOINTS_TYPES[oxpoints_type]]
            entity.update_all_types_completion()
        

        
if __name__ == '__main__':
    OxpointsMapsProvider().import_data()