"""
class Feature

Defines properties of each suggested feature
"""

from django.db import models
from django.core.urlresolvers import reverse


class Feature(models.Model):
    user_name = models.TextField(verbose_name='Your name')
    user_email = models.EmailField(verbose_name='E-mail address')

    title = models.TextField(verbose_name='Feature title')
    description = models.TextField(verbose_name='Description')

    up_vote = models.IntegerField(default=0)
    down_vote = models.IntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    last_commented = models.DateTimeField(blank=True, null=True)

    is_public = models.BooleanField(default=False)
    is_removed = models.BooleanField(default=False)

    class Meta:
        ordering = ('-last_commented', '-created')

    def __unicode__(self):
        return self.title

    @property
    def net_votes(self):
        return self.up_vote - self.down_vote

    def get_absolute_url(self):
        return reverse('feature_vote:feature-detail', args=[self.id])
