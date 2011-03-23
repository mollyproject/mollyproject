from datetime import datetime, timedelta

from molly.conf import app_by_application_name

def geolocation(request):
    """
    Provides location-based information to the template (i.e. lat/long, google
    placemark data, and whether we would like to request the device's location
    information.
    """

    # Use the epoch in the place of -inf; a time it has been a while since.
    epoch = datetime(1970,1,1, 0, 0, 0)
    
    # Only request a location if our current location is older than one minute
    # and the user isn't updating their location manually.
    # The one minute timeout applies to the more recent of a request and an
    # update.
    
    location = request.session.get('geolocation:location')
    requested = request.session.get('geolocation:requested', epoch)
    updated = request.session.get('geolocation:updated', epoch)
    method = request.session.get('geolocation:method')

    period = getattr(app_by_application_name('molly.geolocation'), 'location_request_period', 180)    
    
    if max(requested, updated) + timedelta(0, period) < datetime.now() \
     and method in ('html5', 'gears', 'html5request', None):
        require_location = True
        request.session['geolocation:requested'] = datetime.now()
    else:
        require_location = False
    return {
        'require_location': require_location,
        'geolocation': {
            'location': request.session.get('geolocation:location'),
            'name': request.session.get('geolocation:name'),
            'accuracy': request.session.get('geolocation:accuracy'),
            'history': request.session.get('geolocation:history'),
            'favourites': request.session.get('geolocation:favourites'),
            'method': request.session.get('geolocation:method'),
        },
        'location_error': request.GET.get('location_error'),
    }