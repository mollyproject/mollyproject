from django.conf import settings
import geolocation

class LocationMiddleware(object):
    def process_request(self, request):

        if 'location' in request.session:
            request.location = request.session['location']
            request.placemark = request.session.get('placemark')
        else:
            request.location = None
            request.placemark = None
