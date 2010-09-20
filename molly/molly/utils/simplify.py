import functools

from django.contrib.gis.geos import Point
from django.core.paginator import Paginator

def simplify_value(value):
    if hasattr(value, 'simplify_for_render'):
        return value.simplify_for_render(simplify_value, simplify_model)
    elif isinstance(value, dict):
        out = {}
        for key in value:
            new_key = key if isinstance(key, (basestring, int)) else str(key)
            try:
                out[new_key] = simplify_value(value[key])
            except NotImplementedError:
                pass
        return out
    elif isinstance(value, (list, tuple, set, frozenset)):
        out = []
        for subvalue in value:
            try:
                out.append(simplify_value(subvalue))
            except NotImplementedError:
                pass
        if isinstance(value, tuple):
            return tuple(out)
        else:
            return out
    elif isinstance(value, (basestring, int, float)):
        return value
    elif isinstance(value, datetime):
        return DateTimeUnicode(value.isoformat(' '))
    elif isinstance(value, date):
        return DateUnicode(value.isoformat())
    elif hasattr(type(value), '__mro__') and models.Model in type(value).__mro__:
        return simplify_model(value)
    elif isinstance(value, Paginator):
        return simplify_value(value.object_list)
    elif value is None:
        return None
    elif isinstance(value, Point):
        return simplify_value(list(value))
    elif hasattr(value, '__iter__'):
        # Iterators may be unbounded; silently ignore elements once we've already had 1000.
        return [simplify_value(item) for item in functools.islice(value, 1000)]
    else:
        raise NotImplementedError
    
def simplify_model(obj, terse=False):
    if obj is None:
        return None
    # It's a Model instance
    if hasattr(obj._meta, 'expose_fields'):
        expose_fields = obj._meta.expose_fields
    else:
        expose_fields = [f.name for f in obj._meta.fields]
    out = {
        '_type': '%s.%s' % (obj.__module__[:-7], obj._meta.object_name),
        '_pk': obj.pk,
    }
    if hasattr(obj, 'get_absolute_url'):
        out['_url'] = obj.get_absolute_url()
    if terse:
        out['_terse'] = True
    else:
        for field_name in expose_fields:
            if field_name in ('password',):
                continue
            try:
                value = getattr(obj, field_name)
                if isinstance(value, models.Model):
                    value = simplify_model(value, terse=True)
                out[field_name] = simplify_value(value)
            except NotImplementedError:
                pass
    return out