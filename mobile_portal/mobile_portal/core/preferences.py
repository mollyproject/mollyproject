try:
    import cPickle as pickle
except ImportError:
    import pickle

from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session


class Preferences(models.Model):
    _data = models.TextField()
    _last_updated = models.DateTimeField(auto_now=True)
    session = models.ForeignKey(Session, null=True)
    user = models.ForeignKey(User, null=True)
    base_preference_set = models.CharField(max_length=

    def acquire_user(self, user):
        if self.user:
            raise AssertionError("Preferences object already has a User associated")
        try:
            other = Preferences.objects.get(user=user)
        except Preferences.DoesNotExist:
            pass
        else:
            self += other

EPOCH = datetime(1970, 1, 1)

class UndefinedPreference(object): pass
class UndefinedPreferenceException(KeyError): pass

class PreferenceSet(object):
    def __init__(self, pickled_data=None, default_preference_set=None, parent_details=None):
        if isinstance(pickled_data, dict):
            self._data = dict(
                (k, (datetime.utcnow(), v)) for (k,v) in pickled_data.items()
            )
        if pickled_data:
            self._data = pickle.loads(pickled_data)
        else:
            self._data = {}
        self._defaults = default_preference_set or EmptyPreferenceSet()
        self._modified = False
        self._parent_details = parent_details


    def __getitem__(self, key):
        my_modified = self._data.get(key, (None, EPOCH))[1]
        default_modifed = self._defaults.get_modified(key)
        
        if max(my_modified, default_modified) == EPOCH:
            raise UndefinedPreferenceException
        if my_modified >= default_modified:
            return self._data[key][0]
        else:
            return self._defaults[key]
        
    def __setitem__(self, key, value):
        if isinstance(value, dict):
            value = PreferenceSet(value, self._defaults.get(key, None), (self, key))
            
        self._data[key] = (
            datetime.utcnow(),
            value,
        )
        self.modified = True
    
    def get_modified(self, key):
        my_modified = self._data.get(key, (None, EPOCH))[1]
        default_modifed = self._defaults.get_modified(key)
        return max(my_modified, default_modified)
    
    def _get_modified(self):
        return self._modified
    def set_key_modified(self, key=None):
        self._modified = True
        if self._parent_details:
            parent_preferences, key = self._parent_details
            parent_preferences.modified = True
            parent_preferences
    modified = property(_get_modified)
    
    def __iter__(self):
        return iter(set(self._data) | set(self._defaults))
        
    def __addi__(self, other):
        for key in other._data:
            if other.get_modified(key) > self.get_modified(key):
                if isinstance(self[key], PreferenceSet):
                    self[key] += other[key]
                else:
                    self[key] = other[key]
                
        
class EmptyPreferenceSet(PreferenceSet):
    def __init__(self):
        pass
    def __getitem__(self, key):
        raise UndefinedPreferenceException
    def __setitem__(self, key, value):
        raise NotImplementedError
    def get_modified(self, key):
        return EPOCH
    @property
    def modified(self):
        return False

