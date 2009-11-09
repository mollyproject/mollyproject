
try:
    import cickle as pickle
except ImportError:
    import pickle

import simplejson, base64

from django.db import models
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session

from preferences import PreferenceSet, EmptyPreferenceSet
from defaults import get_defaults, DEFAULTS_CHOICES

class Preferences(models.Model):
    session_key = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, null=True)
    _preference_set_pickled = models.TextField()
    default_preferences = models.CharField(max_length = 10, choices = DEFAULTS_CHOICES)

    def acquire_user(self, user):
        if self.user:
            raise AssertionError("Preferences object already has a User associated")
        try:
            other = Preferences.objects.get(user=user)
        except Preferences.DoesNotExist:
            pass
        else:
            self.preference_set += other.preference_set
        self.session = None
        self.save()

    def _get_preference_set(self):
        try:
            return self._preference_set
        except AttributeError:
            if not self.default_preferences:
                self.default_preferences = 'new'
            if self._preference_set_pickled:
                self._preference_set = pickle.loads(base64.b64decode(self._preference_set_pickled))
            else:
                self._preference_set = PreferenceSet({}, self.default_preferences, get_defaults=get_defaults)
            return self._preference_set
    def _set_preference_set(self, value):
        self._preference_set = value
    preference_set = property(_get_preference_set, _set_preference_set)

    def save(self, *args, **kwargs):
        self._preference_set_pickled = base64.b64encode(pickle.dumps(self.preference_set))
        super(Preferences, self).save(*args, **kwargs)



