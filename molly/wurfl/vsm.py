from math import sqrt
import time

from pywurfl.algorithms import Algorithm
from molly.wurfl.wurfl_data import devices

class Vector(object):
    terms = {}
    def __init__(self, value):
        if isinstance(value, tuple):
            self.value = value
        elif isinstance(value, dict):
            self.value = []
            for term, magnitude in value.items():
                if not term in Vector.terms:
                    Vector.terms[term] = len(Vector.terms)
                self.value.append((Vector.terms[term], magnitude))
            self.value = tuple(sorted(self.value))
        else:
            raise TypeError("Initialise with tuple or dict, not %s" % type(value))
    
    def __add__(self, other):
        out, i, j, u, v = [], 0, 0, self.value, other.value
        try:
            while True:
                if u[i][0] < v[j][0]:
                    i += 1
                    out.append( ( i, u[i][1] ) )
                elif u[i][0] > v[j][0]:
                    j += 1
                    out.append( ( i, v[j][1] ) )
                else:
                    i, j = i+1, j+1
                    out.append( ( i, u[i][1]+v[j][1] ) )
        except IndexError:
            return Vector(tuple(out))
   
    def __sub__(self, other):
        out, i, j, u, v = [], 0, 0, self.value, other.value
        try:
            while True:
                if u[i][0] < v[j][0]:
                    i += 1
                    out.append( ( i, u[i][1] ) )
                elif u[i][0] > v[j][0]:
                    j += 1
                    out.append( ( i, -v[j][1] ) )
                else:
                    i, j = i+1, j+1
                    out.append( ( i, u[i][1]-v[j][1] ) )
        except IndexError:
            return Vector(tuple(out))
   
    def __div__(self, other):
        return Vector(tuple((k,v/other) for (k,v) in self.value))
       
    def __mul__(self, other):
        if isinstance(other, Vector):
            out, i, j, u, v = 0, 0, 0, self.value, other.value
            try:
                while True:
                    if u[i][0] < v[j][0]:
                        i += 1
                    elif u[i][0] > v[j][0]:
                        j += 1
                    else:
                        i, j = i+1, j+1
                        out += u[i][1]*v[j][1]
            except IndexError:
                return out
        else:
            return Vector(tuple((k,v*other) for (k,v) in self.value))
        
    def __abs__(self):
        return sqrt(sum(v**2 for k,v in self.value))

def tokenise(ua):
    for c in ';()':
        ua = ua.replace(c, ' ')
    
    out = []
    for token in ua.split(' '):
        if not token:
            continue
            
        for c in '/.':
            token = token.replace(c, ' ')
        token = token.split()

        for i in range(1, len(token)+1):
            out.append(' '.join(token[:i]))
            out.append(token[i-1])
            
    return out

class VectorSpaceAlgorithm(Algorithm):
    
    use_normalized_ua = True
    
    def __init__(self, devices=None):
        
        if devices:
            self.precompute(devices)
        else:
            self.devices = None
            
    def precompute(self, devices):
        vectors = {}
        for ua, device in devices.devuas.items():
            tokenised = tokenise("%s %s %s" % (ua, device.brand_name, device.model_name))
            vectors[device] = Vector(dict((token, 1) for token in tokenised))
            vectors[device] /= abs(vectors[device])
            
        self.cache = {}
        self.vectors = vectors
        self.devices = devices
        
        
    def __call__(self, ua, devices=None):
        if not devices is None and devices != self.devices:
            self.precompute(devices)
            
        if ua in self.cache:
            return self.cache[ua]
            
        v1 = Vector(dict((token, 1) for token in tokenise(ua)))
        v1 /= abs(v1)
        
        current_device, value = None, float('-inf')
        
        for device, v2 in self.vectors.items():
            c = v1 * v2
            if c > value:
                current_device = device
                value = c
                v = v2
                
        self.cache[ua] = current_device
        return current_device

vsa = VectorSpaceAlgorithm(devices)
