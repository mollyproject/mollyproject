from django import template

from molly.apps.search.forms import SearchForm

register = template.Library()

@register.tag
def search_form(parser, token):
    return SearchFormNode(*token.split_contents()[1:])
    
class SearchFormNode(template.Node):
    """
    Adds a SearchForm instance to the context.
    """

    def __init__(self, prefix=None, name="search_form"):
        self.prefix = prefix
        self.name = name
        
    def render(self, context):
        context[self.name] = SearchForm(prefix=self.prefix)
        return ''
