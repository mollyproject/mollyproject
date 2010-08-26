from lxml import etree

from django.core.urlresolvers import reverse
from django.template import loader, Context

def safe_href(context, url):
    url = url[0]
    return url.startswith('http://') or url.startswith('https://') or url.startswith('ftp://')

def url_func(context, node, name, *args):
    args = [arg.split('#')[0] for arg in args if arg]
    return reverse(name, args=args)

def transform(document, template_name, template_context=None):

    ns = etree.FunctionNamespace('http://mollyproject.org/xpath#')
    ns.prefix = 'molly'
    ns['url'] = url_func
    ns['safe-href'] = safe_href

    # Load a template and turn it into an XSL template
    template = loader.get_template(template_name)
    template = template.render(Context(template_context or {}))
    template = etree.XSLT(etree.XML(template))

    return template(document)

def add_children_to_context(document, context):
    for node in document.findall('*'):
        context[node.tag] = etree.tostring(node, method="html")[len(node.tag)+2:-len(node.tag)-3]
