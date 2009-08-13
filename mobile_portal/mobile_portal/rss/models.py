from django.db import models



class RSSFeed(models.Model):
    title = models.TextField()
    unit = models.CharField(max_length=10,null=True,blank=True)
    rss_url = models.URLField()
    
