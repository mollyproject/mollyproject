from __future__ import division
import random, urllib, os, StringIO
from PIL import Image
from os.path import exists, join
import simplejson
from datetime import datetime, timedelta
from django.contrib.gis.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from molly.maps.models import Entity
import django.dispatch

class Config(models.Model):
    key = models.SlugField()
    value = models.TextField()
    
class ExternalImage(models.Model):
    url = models.URLField()
    etag = models.TextField(null=True)
    last_modified = models.TextField(null=True)
    last_updated = models.DateTimeField() # This one is in UTC
    width = models.PositiveIntegerField(null=True)
    height = models.PositiveIntegerField(null=True)
    
    def save(self, force_insert=False, force_update=False):
        self.last_updated = datetime.utcnow()
        super(ExternalImage, self).save(force_insert=False, force_update=False)

def get_external_image_dir():
    return getattr(settings, 'EXTERNAL_IMAGE_DIR', os.path.join(settings.CACHE_DIR, 'external_images'))

class ExternalImageSized(models.Model):
    external_image = models.ForeignKey(ExternalImage)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    slug = models.SlugField()

    def get_filename(self):
        external_image_dir = get_external_image_dir()
        if not self.slug:
            while not self.slug or ExternalImageSized.objects.filter(slug=self.slug).count():
                self.slug = "%08x" % random.randint(0, 16**8-1)
        if not os.path.exists(external_image_dir):
            os.makedirs(external_image_dir)
        return os.path.join(external_image_dir, self.slug)

    def get_absolute_url(self):
        return reverse('core:external_image', args=[self.slug])    

    def save(self, force_insert=False, force_update=False):
        if not self.id:
            im = Image.open(StringIO.StringIO(urllib.urlopen(self.external_image.url).read()))
            
            size = im.size
            ratio = size[1] / size[0]
            
            if self.width >= size[0]:
                resized = im
            else:
                resized = im.resize((self.width, int(round(self.width*ratio))), Image.ANTIALIAS)
            self.width, self.height = resized.size

            try:            
                resized.save(self.get_filename(), format='jpeg')
            except IOError:
                resized.convert('RGB').save(self.get_filename(), format='jpeg')

            self.external_image.width = size[0]
            self.external_image.height = size[1]
            
        super(ExternalImageSized, self).save(force_insert=False, force_update=False)
  
    def delete(self):
        os.unlink(self.get_filename())
        super(ExternalImageSized, self).delete()

class BlogArticle(models.Model):
    updated = models.DateTimeField()
    html = models.TextField()
    guid = models.TextField()

class UserMessage(models.Model):
    session_key = models.TextField()
    message = models.TextField()
    read = models.BooleanField(default=False)
    when = models.DateTimeField(auto_now_add=True)
    
class ShortenedURL(models.Model):
    path = models.TextField()
    slug = models.TextField(max_length=7)
    
    def get_absolute_url(self):
        return reverse('core_shortened_url_redirect', args=[self.slug])
