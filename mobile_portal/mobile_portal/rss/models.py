from django.db import models

class ShowPredicate(models.Model):
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    predicate = models.TextField()

class RSSFeed(models.Model):
    title = models.TextField()
    unit = models.CharField(max_length=10,null=True,blank=True)
    rss_url = models.URLField()
    slug = models.SlugField()
    last_modified = models.DateTimeField() # this one is in UTC
    
    show_predicate = models.ForeignKey(ShowPredicate, null=True, blank=True)
    
class RSSItem(models.Model):
    feed = models.ForeignKey(RSSFeed)
    title = models.TextField()
    guid = models.TextField()
    description = models.TextField()
    link = models.URLField()
    last_modified = models.DateTimeField() # this one is also in UTC