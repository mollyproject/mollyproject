from django.db import models

WEBCAM_WIDTHS = (100, 300, 200)

class Webcam(models.Model):
    slug = models.SlugField()
    url = models.URLField()
    fetch_period = models.PositiveIntegerField()
    title = models.TextField()
    description = models.TextField(null=True)
    credit = models.TextField(null=True)

    class Meta:
        ordering = ('title',)
