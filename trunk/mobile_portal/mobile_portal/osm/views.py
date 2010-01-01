import pytz, simplejson, urllib2, base64
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from mobile_portal.core.handlers import BaseView
from mobile_portal.core.breadcrumbs import *
from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.utils import AnyMethodRequest

from mobile_portal.oxpoints.models import Entity

from .models import GeneratedMap

def generated_map(request, hash):
    gm = get_object_or_404(GeneratedMap, hash=hash)
    response = HttpResponse(open(gm.get_filename(), 'r').read(), mimetype='image/png') 
    last_updated = pytz.utc.localize(gm.generated)
    
    response['ETag'] = hash
    return response

class MetadataView(BaseView):
    breadcrumb = NullBreadcrumb
    
    api_url = 'http://api.openstreetmap.org/api/0.6/'

    def handle_GET(cls, request, context, ptype):
        ptypes = {
            'restaurant': ('name', 'operator', 'cuisine', 'phone', 'opening_hours'),
            'post_box': ('ref', 'collection_times'),
            'pub': ('name', 'operator', 'food', 'real_ale', 'opening_hours', 'phone'),
            'bar': ('name', 'operator', 'food', 'real_ale', 'opening_hours', 'phone'),
            'place_of_worship': ('name', 'religion', 'denomination', 'phone'),
            'pharmacy': ('name', 'operator', 'dispensing', 'phone', 'opening_hours'),
            'bank': ('name', 'operator', 'phone', 'opening_hours', 'atm'),
            'atm': ('name', 'operator', 'opening_hours'),
            'cafe': ('name', 'operator', 'phone', 'food', 'opening_hours'),
            'ice_cream': ('name', 'operator', 'phone', 'food', 'opening_hours'),
            'bicycle_parking': ('operator', 'capacity'),
            'doctors': ('name', 'operator', 'phone', 'opening_hours'),
            'library': ('name', 'operator', 'phone', 'opening_hours'),
            'parking': ('name', 'operator', 'capacity'),
            'cinema': ('name', 'operator', 'phone', 'opening_hours'),
            'hospital': ('name', 'operator', 'phone', 'opening_hours'),
            'theatre': ('name', 'operator', 'phone', 'opening_hours'),
            'post_office': ('name', 'operator', 'phone', 'opening_hours'),
        }
        context['ptypes'] = ptypes.keys()
        try:
            context['tags'] = tags = ptypes[ptype]
        except KeyError:
            raise Http404

        context['entities'] = []
        for entity in Entity.objects.filter(entity_type__slug=ptype):
            context['entities'].append((entity, [(x, entity.metadata['tags'].get(x, '')) for x in tags]))
        return mobile_render(request, context, 'osm/metadata')

    def handle_POST(cls, request, context, ptype):
        data = simplejson.loads(request.raw_post_data)
        print data
        #return HttpResponse(simplejson.dumps({
        #    'status': 'Debug',
        #    'changes': {},
        #}));
        
        auth = 'Basic ' + base64.b64encode(':'.join((data['username'], data['password'])))
        
        request_data  = '<osm><changeset>'
        request_data += '  <tag k="created_by" v="Mobile Oxford"/>'
        request_data += '  <tag k="comment" v="%s"/>' % escape(data['comment'])
        request_data += '</changeset></osm>'
        request = AnyMethodRequest(cls.api_url+'changeset/create',
                                   data=request_data,
                                   method='PUT')
        request.headers['Authorization'] = auth
        try:
            response = urllib2.urlopen(request)
        except Exception, e:
            return HttpResponse(simplejson.dumps({
                'status': 'There was an error opening the changeset; please check your username and password: %s' % e.read(),
                'changes': {},
            }))
        changeset = response.read()
        print 'CS', changeset
        
        osmchange = cls.get_osmchange(data['changes'], changeset)
        
        request = AnyMethodRequest(cls.api_url+'changeset/%s/upload'%changeset,
                                   data=osmchange,
                                   method='POST')
        request.headers['Authorization'] = auth
        try:
            response = urllib2.urlopen(request)
        except Exception, e:
            print "error 2"
            return HttpResponse(simplejson.dumps({
                'status': 'There was an error uploading the diff: %s' % e.read(),
                'changes': {},
            }))
                    
        diffResult = ET.parse(response)
        updated_entities = {}
        for c in diffResult.getroot():
            id = '%s%s' % (c.tag[0].upper(), c.attrib['old_id'])
            metadata = data['changes'][id]
            metadata['version'] = c.attrib['new_version']
            updated_entities[id] = metadata
            
            entity = Entity.objects.get(osm_id=id)
            entity.metadata['attrs']['version'] = metadata['version']
            entity.metadata['tags'] = metadata['tags']
            entity.save()
        
        request = AnyMethodRequest(cls.api_url+'changeset/%s/close'%changeset,
                                   method='PUT')
        request.headers['Authorization'] = auth
        try:
            response = urllib2.urlopen(request)
        except Exception, e:
            return HttpResponse(simplejson.dumps({
                'status': 'There was an error closing the changeset: %s' % e.read(),
                'changes': {},
            }))
                    
        return HttpResponse(simplejson.dumps({
            'status': 'Upload complete: <a href="%schangeset/%s">changeset</a>' % (cls.api_url, changeset),
            'changes': updated_entities,
        }))
        
    def get_osmchange(cls, data, changeset):
        osmChange = ['<osmChange version="0.3" generator="MobileOxford">\n']
        osmChange.append('  <modify version="0.3" generator="MobileOxford">\n')
        for id, datum in data.items():
            if not id.startswith('N'):
                continue
            values = {
                'id': id[1:],
                'changeset': changeset,
                'version': datum['version'],
                'lon': datum['location'][0],
                'lat': datum['location'][1],
            }
            osmChange.append('    <node id="%(id)s" changeset="%(changeset)s" version="%(version)s" lat="%(lat)s" lon="%(lon)s">\n' % values)
            for key, value in datum['tags'].items():
                if not value:
                    continue
                osmChange.append('      <tag k="%s" v="%s"/>\n' % (escape(key), escape(value)))
            osmChange.append('    </node>\n')
        osmChange.append('  </modify>\n')
        osmChange.append('</osmChange>\n')
        return ''.join(osmChange)
        