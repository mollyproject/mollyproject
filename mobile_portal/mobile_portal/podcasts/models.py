from django.db import models
from django.core.urlresolvers import reverse

class PodcastCategory(models.Model):
    code = models.TextField()
    name = models.TextField()
    
    def get_absolute_url(self):
        return reverse('podcasts_category', args=[self.code])
        
    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name = 'Podcast category'
        verbose_name_plural = 'Podcast categories'
        ordering = ('name',)

class Podcast(models.Model):
    title = models.TextField()
    description = models.TextField()
    rss_url = models.URLField()
    last_updated = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(PodcastCategory)
    
    def get_absolute_url(self):
        return reverse('podcasts_podcast', args=[self.category.code, self.id])
        
    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = 'Podcast feed'
        verbose_name_plural = 'Podcast feeds'
        ordering = ('title',)


class PodcastItem(models.Model):
    podcast = models.ForeignKey(Podcast)
    title = models.TextField()
    description = models.TextField()
    published_date = models.DateTimeField()
    author = models.TextField(null=True, blank=True)
    duration = models.PositiveIntegerField(null=True)
    guid = models.TextField()

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = 'Podcast item'
        verbose_name_plural = 'Podcast items'


class PodcastEnclosure(models.Model):
    podcast_item = models.ForeignKey(PodcastItem)
    url = models.URLField()
    length = models.IntegerField()
    mimetype = models.TextField()
    
    class Meta:
        verbose_name = 'Podcast enclosed data'
        verbose_name_plural = 'Podcast enclosed data'

