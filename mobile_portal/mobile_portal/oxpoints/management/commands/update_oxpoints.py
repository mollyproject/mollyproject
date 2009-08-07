import rdflib
from django.core.management.base import NoArgsCommand
from django.contrib.gis.geos import Point
from mobile_portal.oxpoints.models import Entity, EntityType

OXPOINTS_NS = 'http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#'

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads OxPoints data from http://m.ox.ac.uk/oxpoints/all.xml"
    
    requires_model_validation = True

    @staticmethod
    def load_entity_types():
        """
        Load the entity types into the database, returning a dictionary from
        rdf types (less the namespace) to EntityType objects.
        """
        
        # Define the types of OxPoints entities we'll be loading
        ENTITY_TYPES = {
            'Building':   ('building', 'University building', 'University buildings'),
            'College':    ('college', 'college or PPH', 'colleges and PPHs'),
            'Department': ('department', 'University department', 'University departments'),
            'Museum':     ('museum', 'museum', 'museums'),
            'Library':    ('library', 'library', 'libraries'),
            'Carpark':    ('carpark', 'University car park', 'University car parks'),
            'Unit':       ('unit', 'unit', 'units'),
        }
    
        entity_types = {}
        for ptype, (slug, verbose_name, verbose_name_plural) in ENTITY_TYPES.items():
            entity_type, created = EntityType.objects.get_or_create(slug=slug)
            entity_type.verbose_name = verbose_name
            entity_type.verbose_name_plural = verbose_name_plural
            entity_type.source = 'oxpoints'
            entity_type.id_field = 'oxpoints_id'
            entity_type.save()
            entity_types[ptype] = entity_type
        return entity_types
    
    @staticmethod
    def get_oxpoints_graph():
        """
        Load the OxPoints data into an RDF graph.
        """
        ALL_OXPOINTS = 'http://m.ox.ac.uk/oxpoints/all.xml'
        g = rdflib.ConjunctiveGraph()
        g.parse(ALL_OXPOINTS)
        return g
    
    @staticmethod
    def update_oxpoints_entity(entity_types, uri, location, title, ptype):
        oxpoints_id = int(uri.split('/')[-1])
        entity, created = Entity.objects.get_or_create(oxpoints_id = oxpoints_id)
        # Parse the location. SRID 4326 is WGS84
        entity.location = Point(*map(float, location.split(' ')), **{'srid':4326})
        entity.title = unicode(title)
        entity.entity_type = entity_types[unicode(ptype)[len(OXPOINTS_NS):]]
        entity.save()
    
    def handle_noargs(self, **options):
        entity_types = Command.load_entity_types()
        graph = Command.get_oxpoints_graph()
    
        # Retrieve those objects from OxPoints that have a location, name and type
        places_with_locations = graph.query("""
            SELECT ?p ?l ?n ?t WHERE {
                ?p <http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#hasLocation> ?a
              . ?a <http://www.opengis.net/gml/pos> ?l
              . ?p <http://purl.org/dc/elements/1.1/title> ?n
              . ?p <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?t  }""")
        
        for place in places_with_locations:
            uri, location = place[:2] 
            Command.update_oxpoints_entity(entity_types, *place)
        
            occupiers = list(graph.query("""
                SELECT ?p ?n ?t WHERE {
                    ?p <http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#primaryPlace> ?l
                  . ?p <http://purl.org/dc/elements/1.1/title> ?n
                  . ?p <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?t
                }""",
                initBindings = {'?l': uri}))
        
            for occupier in occupiers:
                uri, title, ptype = occupier
                Command.update_oxpoints_entity(entity_types, uri, location, title, ptype)
