from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop

from molly.apps.podcasts.data import licenses
from molly.external_media import resize_external_image
from molly.utils.i18n import name_in_language

MEDIUM_CHOICES = (
    ('audio', _('audio')),
    ('video', _('video')),
    ('document', _('document')),
)

class PodcastCategory(models.Model):
    slug = models.SlugField()
    order = models.IntegerField(null=True)
    
    @property
    def name(self):
        return name_in_language(self, 'name')
    
    def get_absolute_url(self):
        return reverse('podcasts:category', args=[self.slug])
        
    def __unicode__(self):
        return self.name or ''
    class Meta:
        verbose_name = _('Podcast category')
        verbose_name_plural = _('Podcast categories')
        ordering = ('order',)


class PodcastCategoryName(models.Model):
    podcast_category = models.ForeignKey(PodcastCategory, related_name='names')
    language_code = models.CharField(max_length=10, choices=settings.LANGUAGES)
    name = models.TextField()
    

class Podcast(models.Model):
    slug = models.SlugField(unique=True)
    title = models.TextField(null=True)
    description = models.TextField(null=True)
    rss_url = models.URLField()
    last_updated = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(PodcastCategory, null=True)
    most_recent_item_date = models.DateTimeField(null=True)
    medium = models.CharField(max_length=8, choices=MEDIUM_CHOICES, null=True)
    provider = models.TextField()
    license = models.URLField(null=True)
    logo = models.URLField(null=True)
    language = models.CharField(max_length=10, choices=settings.LANGUAGES,
                                null=True)
    
    def get_absolute_url(self):
        return reverse('podcasts:podcast', args=[self.slug])
        
    def __unicode__(self):
        return self.title or ''
    
    @property
    def license_data(self):
        return licenses.get(self.license)

    class Meta:
        verbose_name = _('Podcast feed')
        verbose_name_plural = _('Podcast feeds')
        ordering = ('title',)
    
    def simplify_for_render(self, simplify_value, simplify_model):
        simplified = simplify_model(self)
        simplified.update({
            'resized_logo': simplify_model(resize_external_image(self.logo, 60))
        })
        return simplified


class PodcastItem(models.Model):
    podcast = models.ForeignKey(Podcast)
    title = models.TextField(null=True)
    description = models.TextField(null=True)
    published_date = models.DateTimeField(null=True)
    author = models.TextField(null=True, blank=True)
    duration = models.PositiveIntegerField(null=True)
    guid = models.TextField()
    order = models.IntegerField(null=True)
    license = models.URLField(null=True)

    def __unicode__(self):
        return self.title or ''
        
    @property
    def license_data(self):
        return licenses.get(self.license) or licenses.get(self.podcast.license)

    class Meta:
        verbose_name = _('Podcast item')
        verbose_name_plural = _('Podcast items')
    
    def simplify_for_render(self, simplify_value, simplify_model):
        return {
            'podcast': simplify_model(self.podcast, terse=True),
            'title': simplify_value(self.title),
            'description': simplify_value(self.description),
            'published_date': simplify_value(self.published_date),
            'author': simplify_value(self.author),
            'duration': simplify_value(self.duration),
            'guid': simplify_value(self.guid),
            'order': simplify_value(self.order),
            'license_data': simplify_value(self.license_data),
            'enclosures': simplify_value(self.podcastenclosure_set.all())
        }

MIMETYPES = {
    'audio/x-mpeg': _('MP3 audio'),
    'video/mp4': _('MP4 video'),
    'MPEG4 Video': _('MP4 video'),
    'text/html': _('HTML document'),
    'audio/mpeg': _('MP3 audio'),
    'video/x-ms-wmv': _('WMV video'),
    'text/plain': _('plain text'),
    'application/pdf': _('PDF document'),
    'audio/x-m4b': _('MP4 audio'),
    'application/octet-stream': _('unknown'),
    'video/mpeg': _('MPEG video'),
    'video/x-m4v': _('MP4 video'),
    'audio/x-m4a': _('MP4 audio'),
    'application/epub+zip': _('ePub eBook')
}    

class PodcastEnclosure(models.Model):
    podcast_item = models.ForeignKey(PodcastItem)
    url = models.URLField()
    length = models.IntegerField(null=True)
    mimetype = models.TextField(null=True)
    
    @property
    def medium(self):
        medium = {
                'application/pdf': ugettext_noop('document'),
                'MPEG4 Video': ugettext_noop('video')
            }.get(self.mimetype)
        if medium:
            return medium
        elif not self.mimetype:
            return self.podcast_item.podcast.medium or ugettext_noop('unknown')
        elif self.mimetype.startswith('audio/'):
            return ugettext_noop('audio')
        elif self.mimetype.startswith('video/'):
            return ugettext_noop('video')
        else:
            return self.podcast_item.podcast.medium or ugettext_noop('unknown')
    
    def get_mimetype_display(self):
        return MIMETYPES.get(self.mimetype, _('unknown'))
    
    class Meta:
        verbose_name = _('Podcast enclosed data')
        verbose_name_plural = _('Podcast enclosed data')
    
    def simplify_for_render(self, simplify_value, simplify_model):
        return {
            'podcast_item': simplify_model(self.podcast_item, terse=True),
            'url': simplify_value(self.url),
            'length': simplify_value(self.length),
            'mimetype': simplify_value(self.mimetype),
            'mimetype_display': simplify_value(self.get_mimetype_display()),
            'medium': simplify_value(self.medium),
        }

