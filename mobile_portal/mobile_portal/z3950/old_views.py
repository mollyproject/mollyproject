def item_detail(request, control_number):

    try:
        zoom = int(request.GET['zoom'])
    except (ValueError, KeyError):
        zoom = None
    else:
        zoom = min(max(10, zoom), 18)

    items = search.ControlNumberSearch(control_number)
    if len(items) == 0:
            raise Http404

    item = items[0]

    location = request.preferences['location']['location']

    points = []

    all_libraries = item.libraries.items()
    libraries, stacks = [], []
    for library, items in all_libraries:
        if library.oxpoints_id and library.oxpoints_entity.is_stack:
            stacks.append( (library, items) )
        else:
            libraries.append( (library, items) )
            
    pprint.PrettyPrinter(indent=4).pprint(all_libraries)

    if libraries:
        entity_ids = set(l.oxpoints_id for l in item.libraries if l.oxpoints_id)
        entities = Entity.objects.filter(oxpoints_id__in = entity_ids)
        if location:
            point = Point(location[1], location[0], srid=4326)
            entities = entities.distance(point).order_by('distance')
    
            ordering = dict((e.oxpoints_id, i) for i, e in enumerate(entities))
    
            libraries.sort(key=lambda l:(ordering[l[0].oxpoints_id] if l[0].oxpoints_id else float('inf')))
    
        else:
            entities.order_by('title')
    
        for library, books in libraries:
            if not (library.oxpoints_id and library.oxpoints_entity.location):
                library.has_location = False
                continue
            color = AVAIL_COLORS[max(b['availability'] for b in books)]
            points.append( (
                library.oxpoints_entity.location[1],
                library.oxpoints_entity.location[0],
                color,
            ) )
            
    
        map_hash, (new_points, zoom) = fit_to_map(
            centre_point = (location[0], location[1], 'green') if location else None,
            points = points,
            min_points = 0 if zoom else len(points),
            zoom = zoom,
            width = request.device.max_image_width,
            height = request.device.max_image_height,
        )
    
        # Yes, this is weird. fit_to_map() groups libraries with the same location
        # so here we add a marker_number to each library to display in the
        # template.
        lib_iter = iter(libraries)
        for i, (a,b) in enumerate(new_points):
            for j in range(len(b)):
                lib_iter.next()[0].marker_number = i + 1
        # Finish off by adding a marker_number for those that aren't on the map.
        # (lib_iter still contains the remaining items after the above calls to
        # next() ).
        for library in lib_iter:
            library[0].marker_number = None

    context = {
        'item': item,
        'libraries': [],
        'map_hash': None,
        'zoom': zoom,
        'stacks': stacks
    }
    
    if libraries:
        context.update({
            'libraries': libraries,
            'map_hash': map_hash,
            'zoom': zoom,
        })
#        
    return mobile_render(request, context, 'z3950/item_detail')
