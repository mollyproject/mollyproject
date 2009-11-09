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
    def __init__(self, data=None, default_preferences=None, parent_details=None, get_defaults=None):
        self._default_preferences = default_preferences
        self.get_defaults = get_defaults
        if default_preferences:
            self._defaults = get_defaults(default_preferences)
        else:
            self._defaults = EmptyPreferenceSet()
 
        def f(k, v):
            if isinstance(v, PreferenceSet):
                dp = self._default_preferences+'/'+k if self._default_preferences else None
                return PreferenceSet(v._data, dp, (self, k), get_defaults=get_defaults)
            else:
                return v
                
        if isinstance(data, dict):
            self._data = dict(
                (k, (d, f(k, v))) for (k,(d,v)) in data.items()
            )
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
                dp = self._default_preferences+'/'+key if self._default_preferences else None
                self._data[key] = (default_modified, PreferenceSet({}, dp, (self, key), get_defaults=self.get_defaults))
                return self._data[key][1]
            else:
                try:
                    self._data[key] = (default_modified, self._defaults[key].copy())
                    return self._data[key][1]
                except Exception, e:
                    return self._defaults[key]
        
    def __setitem__(self, key, value):
        self._data[key] = (
            datetime.utcnow(),
            value,
        )
        self.set_key_modified(key)

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
        self._data[key] = datetime.utcnow(), self._data[key][1]
        if self._parent_details:
            pd = self._parent_details
            parent_preferences, key = self._parent_details
            parent_preferences.set_key_modified(key)
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

    def __getinitargs__(self):
        return self._data, self._default_preferences, self._parent_details, self.get_defaults 
        
    def __getstate__(self):
        return self.__getinitargs__()
    def __setstate__(self, dict):
        self.__init__(*dict)
       
    
    def get_pickled(self):
        return pickle.dumps(self)
        
    def __repr__(self):
        return u"PreferenceSet({%s})" % ", ".join("%s: %s" % (repr(k), repr(self[k])) for k in self)
    __unicode__ = __repr__
        
class _EmptyPreferenceSet(PreferenceSet):
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
    def __getinitargs__(self):
        return ()
    @property
    def modified(self):
        return False
        
eps = _EmptyPreferenceSet()
def EmptyPreferenceSet():
    return eps