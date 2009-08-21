try:
    import cPickle as pickle
except ImportError:
    import pickle

import sys
from datetime import datetime

EPOCH = datetime(1970, 1, 1)

class UndefinedPreference(object): pass
class UndefinedPreferenceException(KeyError): pass

class PreferenceSet(object):
    def __init__(self, pickled_data=None, default_preference_set=None, parent_details=None):
        self._defaults = default_preference_set or EmptyPreferenceSet()
        def f(k, v):
            if isinstance(v, PreferenceSet):
                try:
                    return PreferenceSet(v._data, self._defaults[k], self)
                except UndefinedPreferenceException:
                    return PreferenceSet(v._data, None, self)
            else:
                return v
                
        if isinstance(pickled_data, dict):
            self._data = dict(
                (k, (d, f(k, v))) for (k,(d,v)) in pickled_data.items()
            )
        elif pickled_data:
            self._data = pickle.loads(pickled_data.encode('utf8'))
        else:
            self._data = {}
        self._modified = False
        self._parent_details = parent_details


    def __getitem__(self, key):
        my_modified = self._data.get(key, (EPOCH, None))[0]
        default_modified = self._defaults.get_modified(key)
        
        if max(my_modified, default_modified) == EPOCH:
            raise UndefinedPreferenceException(key)
        if my_modified >= default_modified:
            return self._data[key][1]
        else:
            if isinstance(self._defaults[key], PreferenceSet):
                return PreferenceSet({}, self._defaults[key], self)
            else:
                try:
                    self._data[key] = (default_modified, self._defaults[key].copy())
                    return self._data[key][1]
                except:
                    return self._defaults[key]
        
    def __setitem__(self, key, value):
        self._data[key] = (
            datetime.utcnow(),
            value,
        )
        self._modified = True

    def items(self):
        return [(key, self[key]) for key in self]    
    
    def get(self, key, default=None):
        try:
            return self[key]
        except UndefinedPreferenceException:
            return default    
    
    def get_modified(self, key):
        my_modified = self._data.get(key, (EPOCH, None))[0]
        default_modified = self._defaults.get_modified(key)
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
        if isinstance(other, EmptyPreferenceSet):
            return
        for key in other._data:
            if other.get_modified(key) > self.get_modified(key):
                if isinstance(self[key], PreferenceSet):
                    self[key] += other[key]
                else:
                    self[key] = other[key]
    
    def get_pickled(self):
        return pickle.dumps(self._data)
        
    def __repr__(self):
        print self._data, self._defaults._data
        return u"PreferenceSet({%s})" % ", ".join("%s: %s" % (repr(k), repr(self[k])) for k in self)
    __unicode__ = __repr__
        
class EmptyPreferenceSet(PreferenceSet):
    def __init__(self):
        self._data = {}
    def __getitem__(self, key):
        raise UndefinedPreferenceException
    def __setitem__(self, key, value):
        raise NotImplementedError
    def get_modified(self, key):
        return EPOCH
    def __addi__(self, other):
        raise NotImplementedError
    def __iter__(self):
        return iter([])
    @property
    def modified(self):
        return False