from django.db import models
from django.core.urlresolvers import reverse
from molly.apps.podcasts.data import licenses

MEDIUM_CHOICES = (
    ('audio', 'audio'),
    ('video', 'video'),
    ('document', 'document'),
)

class PodcastCategory(models.Model):
    slug = models.SlugField()
    name = models.TextField()
    order = models.IntegerField(null=True)
    
    def get_absolute_url(self):
        return reverse('podcasts:category', args=[self.slug])
        
    def __unicode__(self):
        return self.name or ''
    class Meta:
        verbose_name = 'Podcast category'
        verbose_name_plural = 'Podcast categories'
        ordering = ('order','name',)

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
    
    def get_absolute_url(self):
        return reverse('podcasts:podcast', args=[self.slug])
        
    def __unicode__(self):
        return self.title or ''
        
    @property
    def license_data(self):
        return licenses.get(self.license)

    class Meta:
        verbose_name = 'Podcast feed'
        verbose_name_plural = 'Podcast feeds'
        ordering = ('title',)


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
        verbose_name = 'Podcast item'
        verbose_name_plural = 'Podcast items'

MIMETYPES = {
    'audio/x-mpeg': 'MP3 audio',
    'video/mp4': 'MP4 video',
    'MPEG4 Video': 'MP4 video',
    'text/html': 'HTML document',
    'audio/mpeg': 'MP3 audio',
    'video/x-ms-wmv': 'WMV video',
    'text/plain': 'plain text',
    'application/pdf': 'PDF document',
    'audio/x-m4b': 'MP4 audio',
    'application/octet-stream': 'unknown',
    'video/mpeg': 'MPEG video',
    'video/x-m4v': 'MP4 video',
    'audio/x-m4a': 'MP4 audio',
    'application/epub+zip': 'ePub eBook'
}    

class PodcastEnclosure(models.Model):
    podcast_item = models.ForeignKey(PodcastItem)
    url = models.URLField()
    length = models.IntegerField(null=True)
    mimetype = models.TextField(null=True)
    
    @property
    def medium(self):
        medium = {'application/pdf': 'document', 'MPEG4 Video': 'video'}.get(self.mimetype)
        if medium:
            return medium
        elif not self.mimetype:
            return self.podcast_item.podcast.medium or 'unknown'
        elif self.mimetype.startswith('audio/'):
            return 'audio'
        elif self.mimetype.startswith('video/'):
            return 'video'
        else:
            return self.podcast_item.podcast.medium or 'unknown'
    
    def get_mimetype_display(self):
        return MIMETYPES.get(self.mimetype, 'unknown')
    
    class Meta:
        verbose_name = 'Podcast enclosed data'
        verbose_name_plural = 'Podcast enclosed data'

