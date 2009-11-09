from os import path
import simplejson

entities = simplejson.loads(open(path.join(path.dirname(__file__), 'all.json')).read().replace(',,', ','))

by_type, by_uri = {}, {}
for entity in entities:
    if not entity['type'] in by_type:
        by_type[entity['type']] = []
    by_type[entity['type']].append(entity)

    by_uri[entity['uri']] = entity

import entity