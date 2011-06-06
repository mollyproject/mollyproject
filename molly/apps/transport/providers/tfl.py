import urllib
from xml.dom import minidom
from django.utils.translation import ugettext as _

from molly.apps.transport.providers import BaseTransitLineStatusProvider

class TubeStatusProvider(BaseTransitLineStatusProvider):
    
    LINESTATUS_URL = 'http://cloud.tfl.gov.uk/TrackerNet/LineStatus'
    
    def get_status(self):
        
        statuses = []
        
        status_xml = minidom.parse(urllib.urlopen(self.LINESTATUS_URL))
        
        for node in status_xml.documentElement.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.tagName == 'LineStatus':
                line_status = {
                    'disruption_reason': node.getAttribute('StatusDetails'),
                }
                for child in node.childNodes:
                    if child.nodeType == child.ELEMENT_NODE and child.tagName == 'Line':
                        line_status['line_id'] = 'tube-%s' % child.getAttribute('ID')
                        line_status['line_name'] = child.getAttribute('Name')
                    elif child.nodeType == child.ELEMENT_NODE and child.tagName == 'Status':
                        line_status['status'] = child.getAttribute('Description')
                statuses.append(line_status)
        
        return {
                'service_name': _('London Underground'),
                'line_statuses': statuses,
            }