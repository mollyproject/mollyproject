from django import template
from django.template.loader import get_template

from molly.maps import map_from_point

register = template.Library()

class MapDisplayNode(template.Node):
    """
    Node to display a more complex map from a @C{molly.maps.Map} object
    """
    
    def __init__(self, map, force_static):
        """
        @param map: The Map to be rendered
        @type map: molly.maps.Map
        """
        self.map = map
        self.force_static = force_static
    
    def render(self, context):
        """
        Returns HTML for the map to be rendered
        
        @type context: dict
        """
        context.update({
                'map': template.Variable(self.map).resolve(context),
                'force_static': self.force_static
            })
        return get_template('maps/embed.html').render(context)


@register.tag
def render_map(parser, token):
    """    
    @raise template.TemplateSyntaxError: If incorrect arguments are passed
    @return: Ready for the map to be rendered
    @rtype: MapDisplayNode
    """
    contents = token.split_contents()
    if len(contents) == 2:
        tag_name, map = contents
        force_static = False
    elif len(contents) == 3:
        tag_name, map, force_static = contents
        force_static = force_static[1:-1] == 'printable'
    else:
        tag_name = token.contents.split()[0]
        raise template.TemplateSyntaxError, \
            "%r tag requires exactly 1 arguments: map" % tag_name
    return MapDisplayNode(map, force_static)


class LocationDisplayNode(template.Node):
    """
    Node to display a simple map with only one location
    """
    
    def __init__(self, place, force_static):
        """
        @param place: Point to render a map for
        """
        self.place = place
        self.force_static = force_static
    
    def render(self, context):
        """
        Returns HTML for the map to be rendered
        
        @type context: dict
        """
        context.update({
           'map': map_from_point(template.Variable(self.place).resolve(context),
                                 context['request'].map_width,
                                 context['request'].map_height,
                                 zoom=context.get('zoom', 16)),
           'force_static': self.force_static
           })
        return get_template('maps/embed.html').render(context)


@register.tag
def render_location_map(parser, token):
    """    
    @raise template.TemplateSyntaxError: If incorrect arguments are passed
    @return: Ready for the map to be rendered
    @rtype: PlaceDisplayNode
    """
    contents = token.split_contents()
    if len(contents) == 2:
        tag_name, place = contents
        force_static = False
    elif len(contents) == 3:
        tag_name, place, force_static = contents
        force_static = force_static[1:-1] == 'printable'
    else:
        tag_name = token.contents.split()[0]
        raise template.TemplateSyntaxError, \
            "%r tag requires exactly 1 arguments: location" % tag_name
    return LocationDisplayNode(place, force_static)

