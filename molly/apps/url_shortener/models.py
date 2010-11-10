from django.db import models
from django.core.urlresolvers import reverse

class ShortenedURL(models.Model):
    path = models.TextField()
    slug = models.TextField(max_length=7)
