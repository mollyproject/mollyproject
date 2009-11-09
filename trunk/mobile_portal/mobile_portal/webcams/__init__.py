from __future__ import division
import PIL.Image
from mobile_portal.core.models import feed_fetched
from models import WEBCAM_WIDTHS

def resize_image(sender, **kwargs):
    if kwargs.get('category') != 'webcam':
        return
        
    path = sender.get_path()
    im = PIL.Image.open(path)
    size = im.size
    ratio = size[1] / size[0]

    
    for width in WEBCAM_WIDTHS:
    
        resized = im.resize((
            width,
            width * ratio
        ))
        
        resized.save("%s-%3d.jpg" % (path, width))

feed_fetched.connect(resize_image)