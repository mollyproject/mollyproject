from xml.sax.saxutils import escape as xml_escape
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

def yesno(s):
    return {'yes':'Yes','no':'No', 'true':'Yes', 'false':'No'}.get(s.lower())
def verbatim(name):
    return lambda t,s,tags: (name, s)

def tag_wifi(t, s, tags):
    return 'wi-fi access', yesno(s)
    
def tag_atm(t, s, tags):
    return 'has ATM', yesno(s)
    
def tag_food(t, s, tags):
    return 'serves food', yesno(s) or s

#def tag_phone(t, s, tags):
#    return 'phone', mark_safe('<a href="tel:%s">%s</a>' % (
#        ''.join(c for c in s if c in '0123456789+'),
#        s.replace('+44-', '0').replace('-', ' '),
#    ))
    
def tag_opening_hours(t, s, tags):
    return 'opening hours', s
#    try:
#        r = [d.split(' ') for d in s.split('; ')]
#        
#    return 

def tag_collection_times(t, s, tags):
    return 'collection times', s

def tag_capacity(t, s, tags):
    try:
        return 'capacity', int(s)
    except:
        return None

def tag_cuisine(t, s, tags):
    try:
        cuisines = [w.capitalize().replace('_', ' ') for w in s.split(';')]
        if len(cuisines) == 1:
            return 'cuisine', ', '.join(cuisines)
        else:
            return 'cuisines', ', '.join(cuisines)
    except:
        return None

#def tag_url(t, s, tags):
#    title = tags.get('url:title', s)
#    return "URL", mark_safe('<a href="%s">%s</a>' % (xml_escape(s), xml_escape(title)))
#def tag_website(t, s, tags):
#    title = tags.get('website:title', s)
#    return "Website", mark_safe('<a href="%s">%s</a>' % (xml_escape(s), xml_escape(title)))

#def tag_wikipedia(t, s, tags):
#    if s.startswith("http://en.wikipedia.org/wiki/"):
#        s = s[29:]
#    return "Wikipedia article", mark_safe('<a href="http://en.m.wikipedia.org/wiki/%s">%s</a>' % (xml_escape(s), xml_escape(tags.get('wikipedia:title', s.replace("_", " ")))))

tag_operator = verbatim('operator')
tag_note = verbatim('note')
    
def tag_dispensing(t, s, tags):
    if t == 'pharmacy':
        return 'dispensing', yesno(s)

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

