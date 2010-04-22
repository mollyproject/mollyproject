import urllib2
from models import ExternalImage, ExternalImageSized

class AnyMethodRequest(urllib2.Request):
    def __init__(self, url, data=None, headers={}, origin_req_host=None, unverifiable=None, method=None):
        self.method = method and method.upper() or None
        urllib2.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)

    def get_method(self):
        if not self.method is None:
            return self.method
        elif self.has_data():
            return "POST"
        else:
            return "GET"

       
def resize_external_image(url, width, timeout=None):
    ei, created = ExternalImage.objects.get_or_create(url=url)

    request = AnyMethodRequest(url, method='HEAD')

    try:
        try:
            response = urllib2.urlopen(request, timeout=timeout)
        except TypeError:
            import socket
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(timeout)
            response = urllib2.urlopen(request)
            socket.setdefaulttimeout(old_timeout)        
    except (urllib2.HTTPError, urllib2.URLError):
        return None

    # Check whether the image has changed since last we looked at it        
    if response.headers.get('ETag', ei.etag) != ei.etag or response.headers.get('Last-Modified', True) != ei.last_modified:

        # Can't use the shorter EIS.objects.filter(...).delete() as that
        # doesn't call the delete() method on individual objects, resulting
        # in the old images not being deleted.
        for eis in ExternalImageSized.objects.filter(external_image=ei):
            eis.delete()
        ei.etag = response.headers.get('Etag')
        ei.last_modified = response.headers.get('Last-Modified')
        ei.save()

    eis, created = ExternalImageSized.objects.get_or_create(external_image=ei, width=width)
    
    return eis
