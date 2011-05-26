from django.db import models

from molly.utils.i18n import name_in_language

WEBCAM_WIDTHS = (100, 300, 200)

class Webcam(models.Model):
    slug = models.SlugField()
    url = models.URLField()
    fetch_period = models.PositiveIntegerField()
    description = models.TextField(null=True)
    credit = models.TextField(null=True)
    
    @property
    def title(self):
        return name_in_language(self, 'title')


class WebcamName(models.Model):
    webcam = models.ForeignKey(Webcam, related_name='names')
    language_code = models.CharField(max_length=10)
    title = models.TextField()