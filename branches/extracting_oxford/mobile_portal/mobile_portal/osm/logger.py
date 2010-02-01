import logging, os.path
from django.conf import settings

def config_logging():
    logger = logging.getLogger('mobile_portal.osm')
    
    filename = os.path.join(settings.LOG_DIR, 'osm')
    if not os.path.exists(filename):
        open(filename, 'w').close()
        
    logger.addHandler(logging.FileHandler(filename))