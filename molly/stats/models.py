from django.db import models
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

class Hit(models.Model):
    
    class Meta:
        permissions = (
            ("can_view", "Can see statistics"),
        )
    
    session_key = models.CharField(max_length=40)

    user_agent = models.TextField(null=True, blank=True)
    device_id = models.TextField(null=True, blank=True)

    ip_address = models.IPAddressField()

    referer = models.TextField(null=True, blank=True)
    full_path = models.TextField()

    requested = models.DateTimeField() # in UTC
    response_time = models.FloatField(null=True, blank=True) # in seconds

    local_name = models.TextField(null=True, blank=True)
    view_name = models.TextField(null=True, blank=True)
    status_code = models.CharField(max_length=3)
    redirect_to = models.TextField(null=True, blank=True)
    traceback = models.TextField(null=True, blank=True)