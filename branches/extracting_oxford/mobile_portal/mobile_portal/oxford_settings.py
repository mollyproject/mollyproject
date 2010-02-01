from mobile_portal.utils import Application

APPLICATIONS = {
    'contact': Application(
        'mobile_portal.contact',
        'mobile_portal.contact.connectors.OxfordXMLConnector',
    ),
}

from mobile_portal.utils import settings