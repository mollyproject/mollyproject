from pytz import utc, timezone
from django.db import models
from django.core.urlresolvers import reverse

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
    
    def __unicode__(self):
        return self.title
        
    def get_absolute_url(self):
        return reverse('rss_item_list', args=[self.slug])
        
    class Meta:
        ordering = ('title',)
    
class RSSItem(models.Model):
    feed = models.ForeignKey(RSSFeed)
    title = models.TextField()
    guid = models.TextField()
    description = models.TextField()
    link = models.URLField()
    last_modified = models.DateTimeField() # this one is also in UTC
    
    @property
    def last_modified_local(self):
        try:
            return utc.localize(self.last_modified).astimezone(timezone('Europe/London'))
        except Exception, e:
            return repr(e)
    
    def get_absolute_url(self):
        return reverse('rss_item_detail', args=[self.feed.slug, self.id])
    class Meta:
        ordering = ('-last_modified',)