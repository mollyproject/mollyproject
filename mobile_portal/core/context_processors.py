from datetime import datetime, timedelta

def geolocation(request):
    epoch = datetime(1970,1,1, 0, 0, 0)
    s = request.session
    if max(s.get('location_requested', epoch), s.get('location_updated', epoch)) + timedelta(0, 300) < datetime.now() and s.get('location_method') in ('geoapi', None):
        require_location = True
        request.session['location_requested'] = datetime.now()
    else:
        require_location = False
    
    location = request.session.get('location')
    placemark = request.session.get('placemark')
    #raise Exception(location)
    
    return {
        'session': request.session.items(),
        'location': location,
        'location_updated': request.session.get('location_updated'),
        'placemark': placemark,
        'require_location': require_location,
    }
