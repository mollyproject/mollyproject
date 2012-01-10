from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from molly.utils.i18n import name_in_language

WEBCAM_WIDTHS = (100, 300, 200)

class Webcam(models.Model):
    
    slug = models.SlugField()
    
    url = models.URLField()
    """
    Represents the original URL of the image for this webcam, except in the case
    of the ``webcam`` view, where url is set to the resized version of the
    image.
    """
    
    fetch_period = models.PositiveIntegerField(help_text=_('in seconds'))
    
    @property
    def title(self):
        """
        The title for this webcam in the current language
        """
        return name_in_language(self, 'title')
    
    @property
    def description(self):
        """
        The description for this webcam in the current language
        """
        return name_in_language(self, 'description')
    
    @property
    def credit(self):
        """
        The credit for this webcam in the current language
        """
        return name_in_language(self, 'credit')


class WebcamName(models.Model):
    webcam = models.ForeignKey(Webcam, related_name='names')
    language_code = models.CharField(max_length=10, choices=settings.LANGUAGES)
    title = models.TextField()
    description = models.TextField()
    credit = models.TextField()
