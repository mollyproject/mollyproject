from dateutil.tz import tzutc, tzlocal
from lxml import etree

from django.core.urlresolvers import reverse
from django.contrib.gis.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from molly.external_media import resize_external_image
from molly.apps.places.models import Entity
from molly.conf.provider import queue_post_save

FEED_TYPE_CHOICES = (
    ('n', 'news'),
    ('e', 'event'),
)


PROVIDER_CHOICES = tuple(
    (provider().class_path, provider().verbose_name)
        for app in settings.APPLICATIONS
        for provider in app.providers
        if app.application_name == 'molly.apps.feeds'
)


FORMAT_CHOICES = tuple((x, x) for x in (
    'lecture', 'class', 'tutorial', 'seminar', 'performance', 'workshop',
    'exhibition', 'meeting',
))


class EventsManager(models.Manager):
    def get_query_set(self):
        return super(EventsManager, self).get_query_set().filter(ptype='e')


class NewsManager(models.Manager):
    def get_query_set(self):
        return super(NewsManager, self).get_query_set().filter(ptype='n')


class Tag(models.Model):
    value = models.CharField(max_length=128)

    def __unicode__(self):
        return self.value


@queue_post_save
class Feed(models.Model):
    title = models.TextField(help_text=_("Feed title"))
    entity = models.ForeignKey(Entity, null=True, blank=True,
                               help_text=_('Place which this feed belongs to'))
    rss_url = models.URLField(help_text=_("URL of feed"),
            verbose_name=_("URL"))
    slug = models.SlugField(help_text=_("Slug of feed, e.g. oucs-news"))
    # this one is in UTC
    last_modified = models.DateTimeField(null=True, blank=True)
    language = models.CharField(max_length=10, choices=settings.LANGUAGES,
                                null=True)

    # Provider type
    ptype = models.CharField(max_length=1, choices=FEED_TYPE_CHOICES)
    provider = models.CharField(max_length=128, choices=PROVIDER_CHOICES)

    objects = models.Manager()
    events = EventsManager()
    news = NewsManager()

    tags = models.ManyToManyField(Tag, blank=True)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        if self.ptype == 'n':
            return reverse('news:item-list', args=[self.slug])
        else:
            return reverse('events:item-list', args=[self.slug])

    class Meta:
        ordering = ('title',)


class vCard(models.Model):
    uri = models.TextField()

    name = models.TextField(blank=True)
    address = models.TextField(blank=True)
    telephone = models.TextField(blank=True)
    location = models.PointField(null=True)
    entity = models.ForeignKey(Entity, null=True, blank=True)


class Series(models.Model):
    feed = models.ForeignKey(Feed)
    guid = models.TextField()
    title = models.TextField()
    unit = models.ForeignKey(vCard, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)


class Item(models.Model):
    feed = models.ForeignKey(Feed)
    title = models.TextField(help_text=_("Title of feed item"))
    guid = models.TextField()
    description = models.TextField(help_text=_("Description of feed item"))
    link = models.URLField(help_text=_("URL to feed item"))
    last_modified = models.DateTimeField(null = True)  # this one is also in UTC

    ptype = models.CharField(max_length=16, choices=FEED_TYPE_CHOICES)

    organiser = models.ForeignKey(vCard, related_name='organising_set',
                                  null=True, blank=True)
    speaker = models.ForeignKey(vCard, related_name='speaking_set',
                                null=True, blank=True)
    venue = models.ForeignKey(vCard, related_name='venue_set',
                              null=True, blank=True)
    contact = models.ForeignKey(vCard, related_name='contact_set',
                                null=True, blank=True)

    series = models.ForeignKey(Series, null=True, blank=True)
    ordinal = models.IntegerField(null=True)
    track = models.TextField(blank=True)

    tags = models.ManyToManyField(Tag, blank=True)

    objects = models.Manager()
    events = EventsManager()
    news = NewsManager()

    dt_start = models.DateTimeField(null=True, blank=True)
    dt_end = models.DateTimeField(null=True, blank=True)
    dt_has_time = models.BooleanField(default=False)

    @property
    def location_mobile_url(self):
        return self.location_url.replace('/reviews/venue/',
                                         '/reviews/phone/venue/')

    @property
    def last_modified_local(self):
        try:
            return self.last_modified.replace(tzinfo=tzutc())\
                .astimezone(tzlocal())
        except Exception, e:
            return repr(e)

    def get_absolute_url(self):
        if self.ptype == 'n':
            return reverse('news:item-detail', args=[self.feed.slug, self.id])
        else:
            return reverse('events:item-detail',
                           args=[self.feed.slug, self.id])

    def get_description_display(self, device):
        html = etree.fromstring('<div>%s</div>' % self.description,
                                parser=etree.HTMLParser())
        for img in html.findall('.//img'):
            eis = resize_external_image(img.attrib['src'],
                                        device.max_image_width - 40)
            if eis != None:
                img.attrib['src'] = eis.get_absolute_url()
                img.attrib['width'] = '%d' % eis.width
                img.attrib['height'] = '%d' % eis.height
        return etree.tostring(html.find('.//div'), method="html")[5:-6]

    def save(self, *args, **kwargs):
        self.ptype = self.feed.ptype
        super(Item, self).save(*args, **kwargs)

    class Meta:
        ordering = ('-last_modified',)
