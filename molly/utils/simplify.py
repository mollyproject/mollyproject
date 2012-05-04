import itertools
import datetime
from logging import getLogger

from lxml import etree

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.core.paginator import Page
from django.db import models
from django.utils.functional import Promise as lazy_translation

logger = getLogger(__name__)


class DateUnicode(unicode):
    pass


class DateTimeUnicode(unicode):
    pass


_XML_DATATYPES = (
    (DateUnicode, 'date'),
    (DateTimeUnicode, 'datetime'),
    (str, 'string'),
    (unicode, 'string'),
    (int, 'integer'),
    (float, 'float'),
)

FIELDS_NOT_EXPOSED = ('password', 'user_email',)


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
                logger.info('Could not simplify field %s of type %s',
                            key, type(value[key]), exc_info=True)
                pass
        return out
    elif isinstance(value, tuple) and hasattr(value, '_asdict'):
        # Handle named tuples as dicts
        return simplify_value(value._asdict())
    elif isinstance(value, (list, tuple, set, frozenset)):
        out = []
        for subvalue in value:
            try:
                out.append(simplify_value(subvalue))
            except NotImplementedError:
                logger.info('Could not simplify a value of type %s',
                            type(subvalue), exc_info=True)
        if isinstance(value, tuple):
            return tuple(out)
        else:
            return out
    elif isinstance(value, (basestring, int, float)):
        return value
    elif isinstance(value, lazy_translation):
        return unicode(value)
    elif isinstance(value, datetime.datetime):
        return DateTimeUnicode(value.isoformat(' '))
    elif isinstance(value, datetime.date):
        return DateUnicode(value.isoformat())
    elif hasattr(type(value), '__mro__') and models.Model in type(value).__mro__:
        return simplify_model(value)
    elif isinstance(value, Page):
        return {
            'has_next': value.has_next(),
            'has_previous': value.has_next(),
            'next_page_number': value.has_next(),
            'previous_page_number': value.has_next(),
            'number': value.number,
            'objects': simplify_value(value.object_list),
            'num_pages': value.paginator.num_pages,
            'num_objects': value.paginator.count,
        }
    elif value is None:
        return None
    elif isinstance(value, Point):
        return simplify_value(list(value))
    elif isinstance(value, Distance):
        # This is here to avoid a circular import
        from molly.utils.templatetags.molly_utils import humanise_distance
        return simplify_value(humanise_distance(value.m))
    elif hasattr(value, '__iter__'):
        # Iterators may be unbounded; silently ignore elements once we've already had 1000.
        return [simplify_value(item) for item in itertools.islice(value, 1000)]
    else:
        raise NotImplementedError


def simplify_model(obj, terse=False):
    if obj is None:
        return None
    # It's a Model instance
    # "expose_fields" is never used
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
            if field_name in FIELDS_NOT_EXPOSED:
                continue
            try:
                value = getattr(obj, field_name)
                if isinstance(value, models.Model):
                    value = simplify_model(value, terse=True)
                out[field_name] = simplify_value(value)
            except NotImplementedError:
                pass

        # Add any non-field attributes
        for field in list(dir(obj)):
            try:
                if field[0] != '_' and field != 'objects' \
                        and not isinstance(getattr(obj, field), models.Field) \
                        and not field in FIELDS_NOT_EXPOSED:
                    try:
                        out[field] = simplify_value(getattr(obj, field))
                    except NotImplementedError:
                        pass
            except AttributeError:
                pass
    return out


def serialize_to_xml(value):
    if value is None:
        node = etree.Element('null')
    elif isinstance(value, bool):
        node = etree.Element('literal')
        node.text = 'true' if value else 'false'
        node.attrib['type'] = 'boolean'
    elif isinstance(value, (basestring, int, float)):
        node = etree.Element('literal')
        try:
            node.text = unicode(value)
        except UnicodeDecodeError:
            # Encode as UTF-8 if ASCII string can not be encoded
            node.text = unicode(value, 'utf-8')
        node.attrib['type'] = [d[1] for d in _XML_DATATYPES if isinstance(value, d[0])][0]
    elif isinstance(value, dict):
        if '_type' in value:
            node = etree.Element('object', {'type': value['_type'], 'pk': unicode(value.get('_pk', ''))})
            del value['_type']
            del value['_pk']
            if '_url' in value:
                node.attrib['url'] = value['_url']
                del value['_url']
            if value.get('_terse'):
                node.attrib['terse'] = 'true'
                del value['_terse']
        else:
            node = etree.Element('collection', {'type': 'mapping'})
        for key in value:
            v = serialize_to_xml(value[key])
            subnode = etree.Element('item', {'key': key})
            subnode.append(v)
            node.append(subnode)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for x, y in ((list, 'list'), (tuple, 'tuple')):
            if isinstance(value, x):
                node = etree.Element('collection', {'type': y})
                break
        else:
            node = etree.Element('collection', {'type': 'set'})
        for item in value:
            v = serialize_to_xml(item)
            subnode = etree.Element('item')
            subnode.append(v)
            node.append(subnode)
    else:
        node = etree.Element('unknown')

    return node
