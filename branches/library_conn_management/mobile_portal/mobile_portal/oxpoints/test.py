import entity
keble = entity.get_resource_by_url('http://m.ox.ac.uk/oxpoints/id/23232373')
print keble
print keble.occupies
print keble.in_images
print keble.primary_place.location

