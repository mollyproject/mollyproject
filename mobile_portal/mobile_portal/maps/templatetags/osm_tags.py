from django import template

register = template.Library()

def yesno(s):
    return {'yes':'Yes','no':'No'}.get(s.lower())
def verbatim(name):
    return lambda t,s: (name, s)

def tag_wifi(t, s):
    return 'wi-fi access', yesno(s)
    
def tag_opening_hours(t, s):
    return 'opening hours', s
#    try:
#        r = [d.split(' ') for d in s.split('; ')]
#        
#    return 

def tag_collection_times(t, s):
    return 'collection times', s

def tag_capacity(t, s):
    try:
        return 'capacity', int(s)
    except:
        return None

def tag_cuisine(t, s):
    try:
        cuisines = [w.capitalize() for w in s.split(';')]
        if len(cuisines) == 1:
            return 'cuisine', ', '.join(cuisines)
        else:
            return 'cuisines', ', '.join(cuisines)
    except:
        return None

tag_operator = verbatim('operator')
tag_note = verbatim('note')
    
def tag_dispensing(t, s):
    if t == 'pharmacy':
        return 'dispensing', yesno(s)

TAGS, funcs = {}, locals().copy()
for func_name in funcs:
    if func_name.startswith('tag_'):
        TAGS[func_name[4:]] = locals()[func_name]

@register.filter(name='osm_tags')
def osm_tags(entity):
    tags = entity.metadata['tags']
    entity_type = entity.entity_type.slug
    
    return_tags = []
    for tag in tags:
        if tag in TAGS:
            return_tag = TAGS[tag](entity_type, tags[tag])
            if not return_tag is None:
                return_tags.append(return_tag)
    
    return return_tags