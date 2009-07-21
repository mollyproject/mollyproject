from django.db import models

# Create your models here.
class Podcast(models.Model):
    title = models.TextField()
    description = models.TextField()
    rss_url = models.URLField()
    last_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return self.title
    
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

class PodcastEnclosure(models.Model):
    podcast_item = models.ForeignKey(PodcastItem)
    url = models.URLField()
    length = models.IntegerField()
    mimetype = models.TextField()
    