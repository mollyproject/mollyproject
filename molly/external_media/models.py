from __future__ import division

import os.path
import random
import urllib
from datetime import datetime
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from PIL import Image

from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse


class ExternalImage(models.Model):
    url = models.URLField()
    etag = models.TextField(null=True)
    last_modified = models.TextField(null=True)
    last_updated = models.DateTimeField() # This one is in UTC
    width = models.PositiveIntegerField(null=True)
    height = models.PositiveIntegerField(null=True)

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self.last_updated = datetime.utcnow()
        super(ExternalImage, self).save(force_insert=False, force_update=False, **kwargs)


def get_external_image_dir():
    return getattr(settings, 'EXTERNAL_IMAGE_DIR', os.path.join(settings.CACHE_DIR, 'external_images'))


class ExternalImageSized(models.Model):
    external_image = models.ForeignKey(ExternalImage)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    slug = models.SlugField()
    content_type = models.TextField()

    def get_filename(self):
        external_image_dir = get_external_image_dir()
        if not self.slug:
            while not self.slug or ExternalImageSized.objects.filter(slug=self.slug).count():
                self.slug = "%08x" % random.randint(0, 16**8-1)
        if not os.path.exists(external_image_dir):
            os.makedirs(external_image_dir)
        return os.path.join(external_image_dir, self.slug)

    def get_absolute_url(self):
        return reverse('external_media:image', args=[self.slug])

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if not self.id:
            response = urllib.urlopen(self.external_image.url)
            data = StringIO(response.read())
            im = Image.open(data)

            size = im.size
            ratio = size[1] / size[0]

            if self.width >= size[0]:
                resized = im
            else:
                try:
                    resized = im.resize((self.width, int(round(self.width*ratio))), Image.ANTIALIAS)
                except IOError, e:
                    if e.message == "cannot read interlaced PNG files":
                        # Ain't nothing can be done until you upgrade PIL to 1.1.7
                        resized = im
                    else:
                        raise
            self.width, self.height = resized.size

            try:
                resized.save(self.get_filename(), format='jpeg')
                self.content_type = 'image/jpeg'
            except IOError, e:
                try:
                    resized.convert('RGB').save(self.get_filename(), format='jpeg')
                    self.content_type = 'image/jpeg'
                except IOError:
                    open(self.get_filename(), 'wb').write(data.getvalue())
                    self.content_type = response.headers['content-type']

            self.external_image.width = size[0]
            self.external_image.height = size[1]

        super(ExternalImageSized, self).save(force_insert=False, force_update=False, **kwargs)

    def delete(self):
        try:
            os.unlink(self.get_filename())
        except OSError:
            # Ignore errors where we're trying to delete a file that's already
            # been deleted
            pass
        super(ExternalImageSized, self).delete()
