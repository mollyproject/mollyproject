from django import template

from molly.apps.weather.models import Weather
from molly.conf.applications import app_by_application_name

register = template.Library()

@register.tag
def weather(parser, token):
    return WeatherNode(*token.split_contents()[1:])
    
class WeatherNode(template.Node):
    """
    Adds a WeatherNode instance to the context.
    """
    
    def __init__(self, name="weather"):
        self.name = name
        
    def render(self, context):
        # Voodoo ahead! Gets the location ID from the molly settings file to use when accessing Weather object.
        try:
            context[self.name] = Weather.objects.get(ptype='o', location_id=app_by_application_name('molly.apps.weather').location_id)
        except Weather.DoesNotExist:
            context[self.name] = None
        return ''
