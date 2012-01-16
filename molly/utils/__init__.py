"""
Contains utility methods to send an e-mail and haversine
"""

import math


def send_email(request, context, template_name, cls=None, to_email=None):
    """
    Sends an e-mail based on a Django template.
    """

    # Imports moved into function because it was causing installer to fail
    # because django may not be installed when installer is running
    # MOLLY-244
    from django.template import Context, RequestContext, loader
    from django.core.mail import EmailMessage
    from django.conf import settings

    if to_email is not None:
        pass
    elif cls and hasattr(cls.conf, 'to_email'):
        to_email = cls.conf.to_email
    else:
        to_email = ('%s <%s>' % admin for admin in settings.MANAGERS)

    if cls and hasattr(cls.conf, 'from_email'):
        from_email = cls.conf.from_email
    else:
        from_email = settings.DEFAULT_FROM_EMAIL

    if request:
        email_context = RequestContext(request, {
            'from_email': from_email,
            'to_email': to_email,
        })
        email_context.update({
            'session_key': request.session.session_key,
            'devid': request.device.devid,
            'ua': request.META.get('HTTP_USER_AGENT'),
            'lon': request.session.get('geolocation:location', (None, None))[0],
            'lat': request.session.get('geolocation:location', (None, None))[1],
            'host': request.META.get('HTTP_HOST'),
            'request': request,
        })
    
    else:
        email_context = Context(request, {
            'from_email': from_email,
            'to_email': to_email,
        })
    
    email_context.update(context)

    template = loader.get_template(template_name)
    email = template.render(email_context)

    headers, last_header = {}, None
    headers_section, body = email.split('\n\n', 1)
    for header in headers_section.split('\n'):
        if header.startswith(' '):
            headers[last_header] += ' ' + header.strip()
        else:
            try:
                key, value = header.split(': ', 1)
                headers[key] = value
                last_header = key
            except ValueError:
                # if the header line isn't in the form Key: Value 
                headers[last_header] += ' ' + header.strip()

    subject = headers.pop('Subject', '[no subject]')
    from_email = headers.pop('from_email', from_email)
    if 'to_email' in headers:
        to_email = (e.strip() for e in headers.pop('to_email').split(';'))

    email = EmailMessage(
        subject = subject,
        body = body,
        from_email = from_email,
        to = to_email,
        headers = headers,
    )

    email.send()
    

def haversine(origin, destination):
    """
    Returns the distance between two points using the haversine formula
    
    http://www.platoscave.net/blog/2009/oct/5/calculate-distance-latitude-longitude-python/
    
    >>> int(haversine((-1.31017, 51.7459), (-1.199226, 51.749327)))
    7647
    """
    
    lon1, lat1 = map(math.radians, origin)
    lon2, lat2 = map(math.radians, destination)
    radius = 6371000 # Earth's radius in metres
    
    dlat = lat2-lat1
    dlon = lon2-lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c
    
    return d
