"""
External Media Package

Used to import and resize media from external sources e.g. RSS feed images.
"""

from lxml import etree
import urllib2
import httplib
import os.path

from molly.utils.xslt import transform
from molly.utils.misc import AnyMethodRequest
from molly.external_media.models import ExternalImage, ExternalImageSized

def sanitise_html(dirty_html, opener=None, device=None):
    html = etree.fromstring("<div>%s</div>" % dirty_html,
                            parser = etree.HTMLParser())
    html = transform(html, 'external_media/html_sanitiser.xslt')

    # serialize and remove the div tag
    return etree.tostring(html, method='html')[5:-6]

def resize_external_image(url, width, timeout=5):

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
    except urllib2.HTTPError as e:
        if e.code in (405, 501):
            try:
                response = urllib2.urlopen(url, timeout=timeout)
            except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException):
                return None
        else:
            return None
    except (urllib2.URLError, httplib.HTTPException):
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

    try:
        eis, created = ExternalImageSized.objects.get_or_create(external_image=ei, width=width)
    except ExternalImageSized.MultipleObjectsReturned:
        for eis in ExternalImageSized.objects.filter(external_image=ei, width=width):
            eis.delete()
        eis, created = ExternalImageSized.objects.get_or_create(external_image=ei, width=width)
    
    if not os.path.exists(eis.get_filename()):
        eis.delete()
        eis, created = ExternalImageSized.objects.get_or_create(external_image=ei, width=width)
    
    return eis
