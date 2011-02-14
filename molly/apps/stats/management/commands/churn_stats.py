from datetime import datetime, timedelta
import pprint, rdflib, dateutil.parser , sys
import cStringIO as StringIO

from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import connection

from molly.wurfl.wurfl_data import devices

class L(unicode):
    def __repr__(self):
        return 'L(%s)' % super(L, self).__repr__()
    def __hash__(self):
        return hash((L, super(L, self)))

# Namespaces
SCV = rdflib.Namespace('http://purl.org/NET/scovo#')
RDF = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
DBP = rdflib.Namespace('http://dbpedia.org/resource/')
MOX = rdflib.Namespace('http://vocab.ox.ac.uk/mox/')
DCT = rdflib.Namespace('http://purl.org/dc/terms/')
FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')
VOID = rdflib.Namespace('http://rdfs.org/ns/void#')
DCAT = rdflib.Namespace('http://www.w3.org/ns/dcat#')
SDMX = rdflib.Namespace('http://proxy.data.gov.uk/sdmx.org/def/sdmx/')
DC = rdflib.Namespace('http://purl.org/dc/elements/1.1/')

DEFINITION = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix scv: <http://purl.org/NET/scovo#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix void: <http://rdfs.org/ns/void#> .
@prefix time: <http://www.w3.org/2006/time#> .
@prefix sdmx: <http://proxy.data.gov.uk/sdmx.org/def/sdmx/> .
@prefix pop: <http://statistics.data.gov.uk/def/population/> .
@prefix year: <http://statistics.data.gov.uk/def/census-year/> .
@prefix mox: <http://vocab.ox.ac.uk/mox/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .

<%(dataset)s>
  a scv:Dataset;
  a void:Dataset;
  a dcat:Dataset;
  dct:title "Usage statistics for {{ site_name }}";
  dct:description "Contains collated statistics of unique devices and user-agents accesing the home page of {{ site_name }} for each month.".

mox:manufacturer rdfs:subPropertyOf scv:dimension;
  rdfs:label "manufacturer";
  rdfs:domain scv:Item;
  rdfs:range foaf:Organization.

mox:userAgent rdfs:subPropertyOf scv:dimension;
  rdfs:label "user agent";
  rdfs:domain scv:Item.

mox:operatingSystem rdfs:subPropertyOf scv:dimension;
  rdfs:label "operating system";
  rdfs:domain scv:Item.
"""

class Command(BaseCommand):
    help = "Generates stats graphs"

    requires_model_validation = True

    option_list = BaseCommand.option_list + (
        make_option('-s', '--start',
            action='store',
            dest='start',
            help='The start date in ISO8601'),
        make_option('-e', '--end',
            action='store',
            dest='end',
            help='The end date in ISO8601'),
        make_option('-d', '--dataset',
            action='store',
            dest='dataset',
            help='The dataset to add items to'),
    )

    manufacturer_topics = {
        'firefox': ('Mozilla', 'Mozilla_Firefox'),
        'safari': ('Apple_Inc.', 'Safari_(web_browser)'),
        'chrome': ('Google', 'Google_Chrome'),
        'Opera': ('Opera_Software', 'Opera_(web_browser)'),
        'opera': ('Opera_Software', 'Opera_(web_browser)'),
        'Nokia': 'Nokia',
        'internet explorer': ('Microsoft', 'Internet Explorer'),
        'HTC': 'HTC_Corporation',
        'Apple': 'Apple_Inc.',
        'Samsung': 'Samsung_Group',
        'SonyEricsson': 'Sony_Ericsson',
        'Ericsson': 'Ericsson',
        'RIM': 'Research_In_Motion',
        'Palm': 'Palm,_Inc.',
        'Sendo': 'Sendo',
        'Siemens': 'Siemens',
        'Nintendo': 'Nintendo',
        'Sagem': 'Sagem',
        'LG': 'LG_Corp.',
        'Sony': 'Sony',
        'Motorola': 'Motorola',
        'ZTE': 'ZTE',
        'Sharp': 'Sharp_Corporation',
        'Philips': 'Philips',
        'Grundig': 'Grundig',
        'Asus': 'Asus',
        'HP': 'Hewlett-Packard',
        'NEC': 'NEC',
        'Lenovo': 'Lenovo',
        'Access': 'Access_Co._Ltd.',
        'Skyworth': 'Skyworth',
    }

    marketing_name_topics = {
        ('HTC', 'Desire'): 'HTC_Desire',
        ('HTC', 'Dream'): 'HTC_Dream',
        ('HTC', 'Pure'): 'HTC_Touch_Diamond2',
        ('HTC', 'Touch Diamond2'): 'HTC_Touch_Diamond2',
        ('SonyEricsson', 'W980v'): 'Sony_Ericsson_W980',
        ('RIM', 'Bold'): 'Blackberry_Bold',
        ('Orange', 'SPV M3100'): ('HTC_Corporation', 'HTC TyTN'),
        ('T-Mobile', 'Dash'): ('HTC_Corporation', 'HTC_Excalibur'),
    }    
    
    model_topics = {
        ('Verizon', 'Droid'): ('Motorola', 'Motorola_Droid'),
        'iPhone': 'iPhone',
        'iPad': 'iPad',
        'iPod Touch': 'iPod_Touch',
        ('HTC', 'Hero'): 'HTC_Hero',
        ('HTC', 'Magic'): 'HTC_Magic',
        ('Palm', 'Pre'): 'Palm_Pre',
        ('Nokia', '5800 XpressMusic'): 'Nokia_5800_XpressMusic',
        ('Nokia', 'E55'): 'Nokia_E55',
        ('Nokia', 'E63'): 'Nokia_E63',
        ('Nokia', 'E70'): 'Nokia_E70',
        ('Nokia', 'E71'): 'Nokia_E71',
        ('Nokia', 'E71x'): 'Nokia_E71',
        ('Nokia', 'N97'): 'Nokia_N97',
        'BlackBerry 8100': 'BlackBerry_Pearl',
        'BlackBerry 8110': 'BlackBerry_Pearl',
        'BlackBerry 8120': 'BlackBerry_Pearl',
        'BlackBerry 8310': 'BlackBerry_Curve_8300',
        'BlackBerry 8900': 'BlackBerry_Curve_8900',
        'BlackBerry 9700': 'BlackBerry_Bold',
        ('Motorola', 'Sholes'): 'Motorola_Droid',
        ('Nintendo', 'DSi'): 'Nintendo_DSi',
        ('Sony', 'PSP'): 'PlayStation_Portable',
        ('Access', 'NetFront Ver. 3.2'): 'NetFront',
        ('T-Mobile', 'G1'): ('HTC_Corporation', 'HTC_Dream'),
        ('Samsung', 'Galaxy'): 'Samsung_i7500',
    }
    
    operating_system_topics = {
        'Nokia': 'Nokia_OS',
        'iPhone OS': 'iOS_(Apple)',
        'Android': 'Android_(operating_system)',
        'Windows Mobile OS': 'Windows_Mobile',
        'RIM OS': 'BlackBerry_OS',
        'webOS': 'WebOS',
        'Symbian OS': 'Symbian_OS',
        'Palm OS': 'Palm_OS',
    }
    
    def dbpedia(self, g, s):
        if s == None:
            return rdflib.BNode()
        if isinstance(s, L):
            n = rdflib.BNode()
            g.add((n, DCT['title'], rdflib.Literal(s)))
        else:
            n = rdflib.URIRef(DBP[s])
        return n
    
    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        start = dateutil.parser.parse(options['start'])
        end = dateutil.parser.parse(options['end'])
        
        cursor.execute("""
            SELECT device_id, COUNT(DISTINCT session_key)
            FROM stats_hit
            WHERE full_path = '/' AND requested >= '%s' AND requested < '%s'
            GROUP BY device_id""" % (start.isoformat(), end.isoformat()))
            
        platforms = {}
        for row in cursor.fetchall():
            device, id_, model = None, row[0], None
            while id_:
                try:
                    device = devices.select_id(id_)
                except:
                    id_ = '_'.join(id_.split('_')[:-1])
                else:
                    break
            else:
                device = devices.select_id('generic')
            
            operating_system = self.operating_system_topics.get(device.device_os, L(device.device_os) or None)
            manufacturer = self.manufacturer_topics.get(device.brand_name, (L(device.brand_name) or None, None))
            if isinstance(manufacturer, tuple):
                manufacturer, model = manufacturer
            if model is None:
                model = self.marketing_name_topics.get((device.brand_name, device.marketing_name))
            if model is None:
                model = self.model_topics.get((device.brand_name, device.model_name))
            if model is None:
                model = self.marketing_name_topics.get(device.marketing_name)
            if model is None:
                model = self.model_topics.get(device.model_name, L(device.model_name) or None)
            if isinstance(model, tuple):
                manufacturer, model = model
                
            sig = (manufacturer, model, operating_system)
            count, device_ids = platforms.get(sig, (0, set()))
            device_ids.add(id_)
            platforms[sig] = count + row[1], device_ids

        g = rdflib.ConjunctiveGraph()
        g.namespace_manager.bind('scv', SCV)
        g.namespace_manager.bind('dct', DCT)
        g.namespace_manager.bind('mox', MOX)
        g.namespace_manager.bind('void', VOID)
        g.namespace_manager.bind('sdmx', SDMX)
        g.namespace_manager.bind('dcat', DCAT)
        g.namespace_manager.bind('dc', DC)
        
        g.parse(StringIO.StringIO(DEFINITION % options), format='n3')
        dataset = rdflib.URIRef(options['dataset'])
        duration = end - start
        time_period = rdflib.BNode()
        g.add((time_period, SCV.min, rdflib.Literal(start)))
        g.add((time_period, SCV.max, rdflib.Literal(end)))
        
        incomplete = {}
        for (manufacturer, model, operating_system), (count, device_ids) in platforms.items():
            item = rdflib.BNode()
            g.add((item, RDF.type, SCV.Item))
            g.add((item, SCV.dataset, dataset))
            g.add((item, RDF.value, rdflib.Literal(int(count))))
            
            g.add((item, MOX.manufacturer, self.dbpedia(g, manufacturer)))
            g.add((item, MOX.userAgent, self.dbpedia(g, model)))
            g.add((item, MOX.operatingSystem, self.dbpedia(g, operating_system)))
            g.add((item, SDMX.timePeriod, time_period))
            
            for device_id in device_ids:
                g.add((item, DC.identifier, rdflib.Literal(device_id)))
            
            if isinstance(manufacturer, L) or isinstance(model, L) or isinstance(operating_system, L):
                incomplete[(manufacturer, model, operating_system)] = count
        
        #pprint.PrettyPrinter().pprint(incomplete)
        print g.serialize(format='pretty-xml')        
