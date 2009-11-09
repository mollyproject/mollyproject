from pytz import utc, timezone
from django.db import models
from django.core.urlresolvers import reverse
from xml.etree import ElementTree as ET
from mobile_portal.core.utils import resize_external_image

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
        
        
    def get_description_display(self, device):
        html = ET.fromstring('<html>%s</html>' % self.description)
        for img in html.findall('.//img'):
            eis = resize_external_image(img.attrib['src'], device.max_image_width-40)
            img.attrib['src'] = eis.get_absolute_url()
            img.attrib['width'] = '%d' % eis.width
            img.attrib['height'] = '%d' % eis.height
        return ET.tostring(html)[6:-7]
            
        
    
    class Meta:
        ordering = ('-last_modified',)