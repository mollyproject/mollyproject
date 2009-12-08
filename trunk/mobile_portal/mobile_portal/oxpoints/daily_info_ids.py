# An OSM ID beginning with an 'N' is a node, a 'W' a way, and an 'R' a
# relation, and can be looked up at OxPoints IDs can be looked up at
# http://www.openstreetmap.org/api/0.6/(node|way|relation)/(?<id>\d+)
# OxPoints IDs can be looked up at http://m.ox.ac.uk/oxpoints/id/(?<id>\d+)

daily_info_ids = {
      80: ('osm',      'N175028262'), # Cape of Good Hope
     265: ('osm',      'N572529574'), # Jericho Tavern
     860: ('osm',      'N282540241'), # New Theatre
     894: ('oxpoints', 23233489),     # Pitt Rivers Museum
     895: ('oxpoints', 23233488),     # Museum of the History of Science
    1000: ('oxpoints', 23232383),     # Lady Margaret Hall
    1001: ('osm',      'W22617426'),  # Westgate Centre
    1003: ('osm',      'N259422967'), # St Cross Church
    1317: ('oxpoints', 23232375),     # O'Reilly Theatre
}