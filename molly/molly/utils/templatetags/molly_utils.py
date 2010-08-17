try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from lxml import etree

from django import template
from django.utils.safestring import SafeUnicode

from molly.utils.xslt import transform

register = template.Library()

@register.filter
def sanitize_html(value, args=''):
    document = etree.parse(StringIO.StringIO('<body>%s</body>' % value), parser = etree.HTMLParser())

    args = args.split(',') + [None, None]
    id_prefix, class_prefix = args[0] or 'sani', args[1] or 'sani'

    document = transform(document, 'utils/sanitize_html.xslt', {
        'id_prefix': id_prefix,
        'class_prefix': class_prefix,
    })
    return SafeUnicode(etree.tostring(document)[6:-7])
