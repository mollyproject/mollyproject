from __future__ import absolute_import
import logging, logging.handlers, os

#format = logging.Formatter("""\
#%(ip_address)s %(requested)s %(referer)r %(full_path)r %(session_key)s \
#%(user_agent)r %(device_id)s %(response_time).5f %(location_method)r \
#%(view_name)r %(status_code)d %(redirect_to)r\
#""")

#handler = logging.StreamHandler(sys.stdout)
#handler.setFormatter(format)
#handler.setLevel(logging.DEBUG)

#logging.getLogger('mobile_portal.core.requests').setLevel(logging.INFO)
#logging.getLogger('mobile_portal.core.requests').addHandler(handler)
#print "Level", logging.getLogger('mobile_portal.core.requests').setLevel(logging.INFO)

if os.environ.get('MP_LOG_TO_SOCKET', 'yes') == 'yes':
    handler = logging.handlers.SocketHandler(
        'localhost',
        logging.handlers.DEFAULT_TCP_LOGGING_PORT
    )
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)