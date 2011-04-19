from django.db import models
from django.contrib.auth.models import User
from django.http import Http404
from django.core.urlresolvers import resolve

class Favourite(models.Model):
    """
    A record of a favourite page
    """
    
    user = models.ForeignKey(User)
    url = models.TextField()