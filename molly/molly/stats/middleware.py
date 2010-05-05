from __future__ import division, absolute_import
from datetime import datetime
import socket, time, logging, sys, traceback
import xml.utils.iso8601

from django.contrib.auth.models import User
from django.conf import settings

from molly.stats.models import Hit


logger = logging.getLogger('mobile_portal.stats.requests')

class StatisticsMiddleware(object):
    def process_request(self, request):

        request.requested = time.time()

    def process_view(self, request, view_func, view_args, view_kwargs):

        request.view_name = ".".join((view_func.__module__, view_func.__name__))

    def process_response(self, request, response):
        logger.info("Request", extra=self.request_details(request, response))
        return response

    def process_exception(self, request, exception):
        details = self.request_details(request)
        details['traceback'] = traceback.format_exc()
        
        logger.error("Uncaught exception", extra=details)
    
    def request_details(self, request, response=None):
        
        view_name = hasattr(request, 'view_name') and request.view_name or None
        
        if hasattr(request, 'device'):
            devid = request.device.devid
        else:
            devid = '-'

        full_path = request.path
        if request.META.get('QUERY_STRING'):
            full_path += '?%s' % request.META['QUERY_STRING']
            
        if hasattr(request, 'session'):
            session_key = request.session.session_key
        else:
            session_key = None

        return {
            'session_key': session_key,
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'device_id': devid,
            'ip_address': request.META['REMOTE_ADDR'],
            'referer': request.META.get('HTTP_REFERER'),
            'full_path': str(full_path),
            'requested': xml.utils.iso8601.tostring(request.requested),
            'response_time': time.time() - request.requested,
            'location_set': getattr(request, 'location_set', False),
            'view_name': view_name,
            'status_code': response.status_code if response else 500,
            'redirect_to': response.get('Location', None) if response else None,
        }
