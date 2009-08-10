from django.db import models
from django.core.urlresolvers import reverse

MEDIUM_CHOICES = (
    ('audio', 'audio'),
    ('video', 'video'),
)

class PodcastCategory(models.Model):
    code = models.TextField()
    name = models.TextField()
    order = models.IntegerField(null=True)
    
    def get_absolute_url(self):
        return reverse('podcasts_category', args=[self.code])
        
    def __unicode__(self):
        return self.name or ''
    class Meta:
        verbose_name = 'Podcast category'
        verbose_name_plural = 'Podcast categories'
        ordering = ('order','name',)

class Podcast(models.Model):
    title = models.TextField(null=True)
    description = models.TextField(null=True)
    rss_url = models.URLField()
    last_updated = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(PodcastCategory, null=True)
    most_recent_item_date = models.DateTimeField(null=True)
    medium = models.CharField(max_length=5, choices=MEDIUM_CHOICES, null=True)
    
    def get_absolute_url(self):
        return reverse('podcasts_podcast', args=[self.category.code, self.id])
        
    def __unicode__(self):
        return self.title or ''

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

    def __unicode__(self):
        return self.title or ''

    class Meta:
        verbose_name = 'Podcast item'
        verbose_name_plural = 'Podcast items'


class PodcastEnclosure(models.Model):
    podcast_item = models.ForeignKey(PodcastItem)
    url = models.URLField()
    length = models.IntegerField(null=True)
    mimetype = models.TextField(null=True)
    
    class Meta:
        verbose_name = 'Podcast enclosed data'
        verbose_name_plural = 'Podcast enclosed data'

