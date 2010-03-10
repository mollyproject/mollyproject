from __future__ import division
from datetime import datetime
import socket

from django.contrib.auth.models import User
from django.conf import settings
from mobile_portal.stats.models import Hit

class StatisticsMiddleware(object):
    def process_request(self, request):

        request.requested = datetime.utcnow()

    def process_view(self, request, view_func, view_args, view_kwargs):

        request.view_name = ".".join((view_func.__module__, view_func.__name__))

    def process_response(self, request, response):
        remote_ip = request.META['REMOTE_ADDR']
        
        try:
            rdns = None
            # rdns = socket.gethostbyaddr(remote_ip)[0].split('.')
            # rdns.reverse()
            # rdns = ".".join(rdns)
        except:
            rdns = None

        response_time = datetime.utcnow() - request.requested
        response_time = response_time.seconds + response_time.microseconds/1e6

        view_name = hasattr(request, 'view_name') and request.view_name or None
        
        if hasattr(request, 'device'):
            devid = request.device.devid
        else:
            devid = '-'

        try:
            user = isinstance(request.user, User) and request.user or None
        except:
            # This will occur when the common middleware has appended a slash
            # or otherwise redirected the request before the auth middleware
            # has added a User object to the request.
            # We're not really interested in these types of request.
            return response
            
        full_path = request.path
        if request.META.get('QUERY_STRING'):
            full_path += '?%s' % request.META['QUERY_STRING']            
            
        hit = Hit.objects.create(
            user = user,
            session_key = request.session.session_key,
            user_agent = request.META.get('HTTP_USER_AGENT'),
            device_id = devid,
            ip_address = remote_ip,
            rdns = rdns,
            referer = request.META.get('HTTP_REFERER'),
            full_path = full_path,
            requested = request.requested,
            response_time = response_time,
            location_method = request.session.get('location_method'),
            location_set = getattr(request, 'location_set', False),
            view_name = view_name,
            status_code = str(response.status_code),
            redirect_to = response.get('Location', None),
        )

        return response
