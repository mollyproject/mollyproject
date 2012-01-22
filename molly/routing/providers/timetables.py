from datetime import datetime, date, timedelta

from django.conf import settings
from django.contrib.gis.geos import LineString
from django.contrib.gis.measure import D
from django.db.models import Q
from django.utils.translation import ugettext as _

from molly.apps.places.models import Entity, EntityGroup, ScheduledStop
from molly.utils import haversine

if not settings.DEBUG:
    raise ImportError("This is a beta provider")

def get_edges(entity, window_start):
    
    print entity, window_start
    
    entity_set = {entity}
    for entity_group in EntityGroup.objects.filter(entity=entity):
        for grouped_entity in entity_group.entity_set.all():
            entity_set.add(grouped_entity)
    
    window_end = window_start + timedelta(minutes=60)
    
    departures = ScheduledStop.objects.filter(
        entity__in=entity_set,
        std__gte=window_start.time(),
        std__lt=window_end.time(),
        activity__in=('O', 'B', 'P'))
    
    departures = [d for d in departures if d.journey.runs_on(window_start.date())]
    
    next = []
    for departure in departures:
        next_stops = ScheduledStop.objects.filter(
            journey=departure.journey,
            order__gt=departure.order,
            activity__in=('B', 'D', 'F')
        ).exclude(entity__in=entity_set)
        next += (
            ((datetime.combine(date.today(), stop.sta) - window_start).total_seconds(),
                stop) for stop in next_stops)
    
    return next

def h(loc1, loc2):
    """
    Assumes humans walk at 1 m/s - in a straight line, potentially through buildings
    """
    if loc1.location is None:
        return float('+inf')
    return haversine(loc1.location, loc2)

def plan_route(start_nodes, end_loc, end_nodes, start_time=datetime.now()):
    """
    Uses A* to plan a route
    """
    
    visited = set()
    to_evaluate = set(ScheduledStop(entity=node) for node in start_nodes)
    to_evaluate_ids = set()
    route = {}
    next_times = dict((node, start_time) for node in start_nodes)
    
    g_score = dict((node, 0) for node in start_nodes)
    h_score = dict((node, h(node, end_loc)) for node in start_nodes)
    f_score = dict((node, h_score[node]) for node in start_nodes)
    
    while len(to_evaluate) > 0:
        next = sorted(to_evaluate, key=lambda s: f_score[s.entity])[0]
        if next.entity in end_nodes:
            route = reconstruct_path(route, route[next.entity]) + [next]
            if route[0].entity in start_nodes:
                route = route[1:]
            return route
        to_evaluate.remove(next)
        if next.id is not None:
            to_evaluate_ids.remove(next.id)
        visited.add(next.entity.id)
        for weight, stop in get_edges(next.entity, next_times[next.entity]):
            if stop.entity.id in visited:
                continue
            tentative_g_score = g_score[next.entity] + weight
            
            if stop.id not in to_evaluate_ids:
                to_evaluate.add(stop)
                to_evaluate_ids.add(stop.id)
                h_score[stop.entity] = h(stop.entity, end_loc)
                tentative_is_better = True
            else:
                tentative_is_better = tentative_g_score < g_score[stop.entity]
            
            if tentative_is_better:
                route[stop.entity] = next
                next_times[stop.entity] = datetime.combine(start_time.date(), stop.sta)
                g_score[stop.entity] = tentative_g_score
                f_score[stop.entity] = g_score[stop.entity] + h_score[stop.entity]
 
    return {
        'error': 'No routes found'
    }

def reconstruct_path(routes, node):
    if node is None:
        return []
    return reconstruct_path(routes, routes.get(node)) + [node]

def generate_route(points, type):
    
    start_time = datetime.now()
    
    def generate_instructions(route, start_points, end_loc):
        waypoints = []
        for scheduled_stop in route:
            start_point = start_points.filter(
                scheduledstop__journey=scheduled_stop.journey
                )[0].scheduledstop_set.filter(
                journey=scheduled_stop.journey)[0]
            
            stops_on_route = ScheduledStop.objects.filter(
                journey=scheduled_stop.journey,
                order__gte=start_point.order,
                order__lte=scheduled_stop.order
            )
            
            if len(waypoints) > 0:
                waypoints[-1]['path'] = LineString(
                    waypoints[-1]['location'], start_point.entity.location 
                )
            
            waypoints.append({
                'instruction': 'Take service %s from %s towards %s (%s)' %
                    (scheduled_stop.journey.route.service_id,
                     start_point.entity.title,
                     scheduled_stop.journey.destination,
                     start_point.std),
                'path': LineString([stop.entity.location for stop in stops_on_route]),
                'location': start_point.entity.location
            })
            waypoints.append({
                'instruction': 'Disembark at %s (%s)' %
                    (scheduled_stop.entity.title, scheduled_stop.sta),
                'location': scheduled_stop.entity.location
            })
            start_points = Entity.objects.filter(
                  Q(groups__in=scheduled_stop.entity.groups.all())
                | Q(id=scheduled_stop.entity.id))
        waypoints[-1]['path'] = LineString(
            waypoints[-1]['location'], end_loc 
        )
        return waypoints
    
    if type != 'public transport':
        return {
            'error': _('Only public transport routes can be mapped')
        }
    
    instructions = []
    transfer_points = []
    
    for i in range(1, len(points)):
        start_access_nodes = Entity.objects.filter(
            all_types_completion__slug='public-transport-access-node',
            location__distance_lt=(points[i-1], D(m=200))
        )
        destination_access_nodes = Entity.objects.filter(
            all_types_completion__slug='public-transport-access-node',
            location__distance_lt=(points[i], D(m=200))
        )
        
        if start_access_nodes.count() == 0:
            return {
                'error': _('Could not find a public transport access node near you')
            }
        
        if destination_access_nodes.count() == 0:
            return {
                'error': _('Could not find a public transport access node near your destination')
            }
        
        route = plan_route(
            start_access_nodes, points[i], destination_access_nodes, start_time)
        if 'error' in route:
            return route
        instructions += generate_instructions(route, start_access_nodes, points[i])
        for instruction in instructions:
            transfer_points += instruction['path']
    
    return {
        'waypoints': instructions,
        'path': LineString(transfer_points),
        'total_time': (datetime.combine(date.today(), route[-1].sta)
                       - start_time).total_seconds(),
        'total_distance': sum(
            haversine(transfer_points[i-1], transfer_points[i])
                for i in range(1, len(transfer_points)))
    }
