from datetime import datetime, timedelta

from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.sessions.models import Session

from molly.apps.home.models import UserMessage
from molly.utils import send_email

class Feature(models.Model):
    user_name = models.TextField(verbose_name=_('Your name'))
    user_email = models.EmailField(verbose_name=_('E-mail address'))

    title = models.TextField(verbose_name=_('Feature title'))
    description = models.TextField(verbose_name=_('Description'))

    up_vote = models.IntegerField(default=0)
    down_vote = models.IntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    last_commented = models.DateTimeField(blank=True, null=True)

    is_public = models.BooleanField(default=False)
    is_removed = models.BooleanField(default=False)
    implemented_on = models.DateTimeField(blank=True, null=True,
                                          verbose_name=_('Date this feature was implemented'))
    notifications_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ('-last_commented', '-created')

    def __unicode__(self):
        return self.title

    REMOVE_AFTER_IMPLEMENTED_FOR = timedelta(weeks=4)

    def check_remove(self, request):
        """
        Marks a feature as removed a month after it's been implemented
        """
        if self.implemented_on and not self.notifications_sent:
            
            # Send notifications that this feature's been implemented
            # First to the original requesting user
            send_email(request, {
                'feature': self,
            }, 'feature_vote/implemented.eml', to_email=(self.user_email,))
            self.notifications_sent = True
            self.save()
            
            # And now, using the developer messages framework, to all voting
            # users
            voting_sessions = set()
            for session in Session.objects.all():
                if 'feature_vote:votes' in session.get_decoded():
                    if self.id in session.get_decoded()['feature_vote:votes']:
                        voting_sessions.add(session.session_key)
            
            for session_key in voting_sessions:
                UserMessage.objects.create(session_key=session_key,
                                           message="A feature you voted on (%s), has now been implemented!" % self.title)
            
        if not self.is_removed and self.implemented_on and \
          self.implemented_on + self.REMOVE_AFTER_IMPLEMENTED_FOR < datetime.now():
            self.is_removed = True
            self.save()

    @property
    def net_votes(self):
        return self.up_vote - self.down_vote

    def get_absolute_url(self):
        return reverse('feature_vote:feature-detail', args=[self.id])
