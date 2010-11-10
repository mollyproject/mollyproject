from __future__ import division, absolute_import

from inspect import isfunction

from datetime import datetime
import socket, time, logging, sys, traceback, Cookie

from django.contrib.auth.models import User
from django.conf import settings
from django.http import Http404
from django.core.exceptions import PermissionDenied

logger = logging.getLogger('molly.stats.requests')

class StatisticsMiddleware(object):
    def process_request(self, request):
        request.requested = time.time()

    def process_view(self, request, view_func, view_args, view_kwargs):

        if isfunction(view_func):
            request._stats_view_name = ".".join((view_func.__module__, view_func.__name__))
        else:
            request._stats_view_name = unicode(view_func)

        try:
            request._stats_local_name = view_func.conf.local_name
        except AttributeError, e:
            request._stats_local_name = None

    def process_response(self, request, response):
        logger.info("Request", extra=self.request_details(request, response))
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            details = self.request_details(request, type('', (dict,), {'status_code':404})())
            logger.info("Request", extra=details)
        if isinstance(exception, PermissionDenied):
            details = self.request_details(request, type('', (dict,), {'status_code':403})())
            logger.info("Request", extra=details)
        else:
            details = self.request_details(request)
            details['traceback'] = traceback.format_exc()
            logger.error("Uncaught exception", extra=details)

    def request_details(self, request, response=None):

        view_name = getattr(request, '_stats_view_name', None)
        local_name = getattr(request, '_stats_local_name', None)

        if hasattr(request, 'device'):
            devid = request.device.devid
        else:
            devid = None

        if hasattr(request, 'session'):
            session_key = request.session.session_key
        else:
            try:
                session_key = Cookie.BaseCookie(request.META.get('HTTP_COOKIE', ''))['sessionid'].value
            except:
                session_key = ''

        requested = getattr(request, 'requested', time.time())

        return {
            'session_key': session_key,
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'device_id': devid,
            'ip_address': request.META['REMOTE_ADDR'],
            'referer': request.META.get('HTTP_REFERER'),
            'full_path': request.get_full_path(),
            'requested': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(requested)) + ('%.6f' % (requested % 1))[1:],
            'response_time': (time.time() - requested) if hasattr(request, 'requested') else None,
            'local_name': local_name,
            'view_name': view_name,
            'status_code': response.status_code if response else 500,
            'redirect_to': response.get('Location', None) if response else None,
        }
