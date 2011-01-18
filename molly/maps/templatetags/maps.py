from django import template
from django.template.loader import get_template

register = template.Library()

class MapDisplayNode(template.Node):
    
    def __init__(self, map):
        """
        @param map: The Map to be rendered
        @type map: molly.maps.Map
        """
        self.map = map
    
    def render(self, context):
        """
        Returns HTML for the map to be rendered
        
        @type context: dict
        """
        context.update({
            'map': template.Variable(self.map).resolve(context)
            })
        return get_template('maps/embed.html').render(context)

@register.tag
def render_map(parser, token):
    """    
    @raise template.TemplateSyntaxError: If incorrect arguments are passed
    @return: Ready for the map to be rendered
    @rtype: MapDisplayNode
    """
    try:
        tag_name, map = token.split_contents()
    except ValueError:
        tag_name = token.contents.split()[0]
        raise template.TemplateSyntaxError, \
            "%r tag requires exactly 1 arguments: map" % tag_name
    return MapDisplayNode(map)