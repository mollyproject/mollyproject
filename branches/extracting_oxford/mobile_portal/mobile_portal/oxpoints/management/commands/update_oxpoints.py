import rdflib, Queue
from django.core.management.base import NoArgsCommand
from django.contrib.gis.geos import Point
from mobile_portal.oxpoints.models import Entity, EntityType


OXPOINTS_NS = 'http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#'

ns_vcard = rdflib.Namespace("http://nwalsh.com/rdf/vCard#")


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads OxPoints data from http://m.ox.ac.uk/oxpoints/all.xml"

    requires_model_validation = True

    def load_entity_types(self):
        """
        Load the entity types into the database, returning a dictionary from
        rdf types (less the namespace) to EntityType objects.
        """

        # Define the types of OxPoints entities we'll be loading
        ENTITY_TYPES = {
            'Building':   ('building', 'University building', 'University buildings', True, True, ''),
            'College':    ('college', 'college or PPH', 'colleges and PPHs', True, True, ''),
            'Department': ('department', 'University department', 'University departments', False, False, ''),
            'Museum':     ('museum', 'museum', 'museums', True, True, ''),
            'Library':    ('ulibrary', 'library', 'libraries', True, True, 'Please note that all libraries have admission and borrowing policies; inclusion in this list does not imply access.'),
            'Carpark':    ('carpark', 'University car park', 'University car parks', True, True, ''),
            'Unit':       ('unit', 'unit', 'units', False, False, ''),
            'Room':       ('room', 'room', 'rooms', True, False, ''),
            'SubLibrary': ('sublibrary', 'library sublocation', 'library sublocations', False, False, ''),
            'DepOrUnit':  ('unitdep', 'university department or unit', 'university departments and units', True, True, ''), 
        }

        entity_types = {}
        for ptype, (slug, verbose_name, verbose_name_plural, show_in_nearby_list, show_in_category_list, note) in ENTITY_TYPES.items():
            entity_type, created = EntityType.objects.get_or_create(slug=slug)
            entity_type.verbose_name = verbose_name
            entity_type.article = 'a'
            entity_type.note = note
            entity_type.verbose_name_plural = verbose_name_plural
            entity_type.source = 'oxpoints'
            entity_type.id_field = 'oxpoints_id'
            entity_type.show_in_nearby_list = show_in_nearby_list
            entity_type.show_in_category_list = show_in_category_list
            entity_type.save()
            entity_types[ptype] = entity_type
            
        entity_types['DepOrUnit'].sub_types.add(entity_types['Department'])
        entity_types['DepOrUnit'].sub_types.add(entity_types['Unit'])
        self.entity_types = entity_types

    def load_oxpoints_graph(self):
        """
        Load the OxPoints data into an RDF graph.
        """
        ALL_OXPOINTS = 'http://m.ox.ac.uk/oxpoints/all.xml'
        g = rdflib.ConjunctiveGraph()
        g.parse(ALL_OXPOINTS)
        self.graph = g

    def update_oxpoints_entity(self, uri, location, title, ptype, depth=0):
        oxpoints_id = int(uri.split('/')[-1])
        print oxpoints_id

        if oxpoints_id in self.seen:
            return
        else:
            self.seen.add(oxpoints_id)

        if depth > 0:
            if location:
                self.counts['with_location_inferred'] += 1
            else:
                self.counts['without_location_inferred'] += 1

        entity, created = Entity.objects.get_or_create(oxpoints_id = oxpoints_id)
        # Parse the location. SRID 4326 is WGS84
        if location:
            entity.location = Point(*map(float, location.split(' ')), **{'srid':4326})
            entity.geometry = entity.location
        entity.title = unicode(title)
        entity.entity_type = self.entity_types[unicode(ptype)[len(OXPOINTS_NS):]]
        entity.all_types.add(entity.entity_type)
        if entity.entity_type.slug in ('unit', 'department'):
            entity.all_types.add(self.entity_types['DepOrUnit'])

        parents = list(self.graph.query("SELECT ?q WHERE { ?p ?r ?q }", initBindings = {
                    '?r': rdflib.URIRef('http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#subsetOf'),
                    '?p': rdflib.URIRef(uri)
        }))

        if len(parents) == 1:
            self.subsetsOf[entity] = parents[0][0][-8:]
            entity.is_sublocation = True

        if entity.entity_type.slug == 'sublibrary':
            entity.is_stack = any((x in entity.title.lower()) for x in ('stack', 'nuneham', 'offsite'))

        # Find the postcode
        post_codes = self.graph.query("""
            SELECT ?p WHERE {
                ?e ?ha ?a
              . ?a ?pc ?p }""",
            initBindings = {
                '?e': uri, '?ha': ns_vcard['adr'], '?pc': ns_vcard['postal_code']
            })
            
        for post_code in post_codes:
            post_code = unicode(post_code[0])
            entity.post_code = post_code.replace(' ', '')
        
        entity.save()

        other_places =  self.graph.query("""
            SELECT ?p ?n ?t ?r WHERE {
                ?p ?r ?q
              . ?p <http://purl.org/dc/elements/1.1/title> ?n
              . ?p <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?t  }""",
            initBindings = {'?q': uri})
        other_places = (p[:3] for p in other_places if p[3] in [
            rdflib.URIRef('http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#primaryPlace'),
            rdflib.URIRef('http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#physicallyContainedWithin'),
            rdflib.URIRef('http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#subsetOf'),
        ])
        
        #print "%s%s%-60s%s %-20s" % (("  " if location else "? "), "  "*depth, title, "  "*(6-depth), ptype[len(OXPOINTS_NS):])
        
        for uri, title, ptype in other_places:
            self.queue.put((uri, location, title, ptype, depth+1))

    def link_subsets_of(self):
        for entity, oxpoints_id in self.subsetsOf.items():
            entity.parent = Entity.objects.get(oxpoints_id = oxpoints_id)
            if entity.entity_type != entity.parent.entity_type:
                entity.is_sublocation = False
            entity.save()

    def handle_noargs(self, **options):
        self.load_entity_types()
        self.load_oxpoints_graph()
        
        self.seen = set()
        self.queue = Queue.Queue()
        self.subsetsOf = {}

        self.counts = {
            'with_location': 0,
            'with_location_inferred': 0,
            'without_location': 0,
            'without_location_inferred': 0,
            'removed': 0,
        }            
    
        # Retrieve those objects from OxPoints that have a location, name and type
        places_with_locations = self.graph.query("""
            SELECT ?p ?l ?n ?t WHERE {
                ?p <http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#hasLocation> ?a
              . ?a <http://www.opengis.net/gml/pos> ?l
              . ?p <http://purl.org/dc/elements/1.1/title> ?n
              . ?p <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?t  }""")
        
        for place in places_with_locations:
            self.queue.put(place)
            self.counts['with_location'] += 1

        while not self.queue.empty():
            self.update_oxpoints_entity(*self.queue.get())
            
        places_without_locations = self.graph.query("""
            SELECT ?p ?n ?t WHERE {
                ?p <http://purl.org/dc/elements/1.1/title> ?n
              . ?p <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?t  }""")
        places_without_locations = (p for p in places_without_locations if (
            p[2].startswith(OXPOINTS_NS) and not int(p[0].split('/')[-1]) in self.seen
        ))
        
        for place in places_without_locations:
            uri, title, ptype = place
            self.queue.put((uri, None, title, ptype))
            self.counts['without_location'] += 1

        while not self.queue.empty():
            self.update_oxpoints_entity(*self.queue.get())
        
        for entity in Entity.objects.filter(entity_type__source='oxpoints'):
            if not entity.oxpoints_id in self.seen:
                entity.delete()
                self.counts['removed'] += 1


        self.link_subsets_of()
  
        
        print self.counts
        print len(self.seen)
        print sum(self.counts.values())
        print sum(self.counts.values()) - self.counts['removed']
        
