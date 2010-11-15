from django.contrib.gis.db import models

class Config(models.Model):
    key = models.SlugField()
    value = models.TextField()

class UserMessage(models.Model):
    session_key = models.TextField()
    message = models.TextField()
    read = models.BooleanField(default=False)
    when = models.DateTimeField(auto_now_add=True)

