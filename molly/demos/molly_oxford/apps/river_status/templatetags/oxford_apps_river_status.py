from django import template

from molly_oxford.apps.river_status.models import FlagStatus

register = template.Library()

@register.tag
def flag_status(parser, token):
    return FlagStatusNode(*token.split_contents()[1:])

class FlagStatusNode(template.Node):
    """
    Adds a FlagStatusNode instance to the context.
    """

    def __init__(self, name="flag_status"):
        self.name = name

    def render(self, context):
        # Voodoo ahead! Gets the location ID from the molly settings file to use when accessing Weather object.
        try:
            context[self.name] = FlagStatus.objects.all()
        except Weather.DoesNotExist:
            context[self.name] = None
        return ''
