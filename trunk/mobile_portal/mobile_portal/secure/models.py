from django.db import models

class RequestToken(models.Model):
    oauth_token = models.TextField()
    oauth_token_secret = models.TextField()
    redirect_to = models.TextField()
    service = models.TextField()