from xml.sax.saxutils import escape as xml_escape
from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

register = template.Library()

def yesno(s):
    return {
        'yes': _('Yes'),
        'no': _('No'),
        'true': _('Yes'),
        'false': _('No')
        }.get(s.lower())

def verbatim(name):
    return lambda t,s,tags: (name, _(s))

def tag_wifi(t, s, tags):
    return _('wi-fi access'), yesno(s)
    
def tag_atm(t, s, tags):
    return _('has ATM'), yesno(s)
    
def tag_food(t, s, tags):
    return _('serves food'), yesno(s) or s
    
def tag_opening_hours(t, s, tags):
    return _('opening hours'), s

def tag_collection_times(t, s, tags):
    return _('collection times'), s

def tag_capacity(t, s, tags):
    try:
        return _('capacity'), int(s)
    except:
        return None

def tag_cuisine(t, s, tags):
    try:
        cuisines = [_(w.capitalize().replace('_', ' ')) for w in s.split(';')]
        if len(cuisines) == 1:
            return _('cuisine'), ', '.join(cuisines)
        else:
            return _('cuisines'), ', '.join(cuisines)
    except:
        return None

tag_operator = verbatim(_('operator'))
tag_note = verbatim(_('note'))
    
def tag_dispensing(t, s, tags):
    if t == 'pharmacy':
        return _('dispensing'), yesno(s)

TAGS, funcs = {}, locals().copy()
for func_name in funcs:
    if func_name.startswith('tag_'):
        TAGS[func_name[4:]] = locals()[func_name]

@register.filter(name='osm_tags')
def osm_tags(entity):
    if not 'osm' in entity.metadata:
        return []
    tags = entity.metadata['osm']['tags']
    entity_type = entity.primary_type.slug
    
    return_tags = []
    for tag in tags:
        if tag in TAGS:
            return_tag = TAGS[tag](entity_type, tags[tag], tags)
            if not return_tag is None:
                return_tags.append(return_tag)
    
    return return_tags

@register.filter(name='osm_tag_wikipedia_uri')
def tag_wikipedia_uri(value):
    if value.startswith("http://en.wikipedia.org/wiki/"):
        value = value[29:]
    return value

