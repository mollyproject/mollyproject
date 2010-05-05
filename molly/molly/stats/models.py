from django.db import models
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

class Hit(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    session_key = models.CharField(max_length=40)

    user_agent = models.TextField(null=True, blank=True)
    device_id = models.TextField()

    ip_address = models.IPAddressField()
    rdns = models.TextField(null=True, blank=True)

    referer = models.TextField(null=True, blank=True)
    full_path = models.TextField()

    requested = models.DateTimeField() # in UTC
    response_time = models.FloatField() # in seconds

    location_method = models.TextField(null=True, blank=True)
    location_set = models.BooleanField()

    view_name = models.TextField(null=True, blank=True)
    status_code = models.CharField(max_length=3)
    redirect_to = models.TextField(null=True,blank=True)
