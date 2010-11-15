from StringIO import StringIO
from xml.sax.saxutils import escape
from xml.etree.ElementTree import Element
from xml.etree import ElementTree as ET
from lxml import etree

VALID_TAGS = set([
    'a', 'abbr', 'address', 'bdo', 'big', 'blockquote', 'br', 'caption', 'cite',
    'code', 'col', 'colgroup', 'dd', 'del', 'div', 'dfn', 'dl', 'dt', 'em',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'img', 'ins', 'kbd', 'li', 'ol', 'p', 'pre',
    'q', 'samp', 'small', 'span', 'strong', 'sub', 'sup', 'table', 'tbody',
    'td', 'tfoot', 'th', 'thead', 'tr', 'tt', 'ul', 'var',
])

REMOVE_IF_EMPTY = set([
    'a', 'abbr', 'address', 'bdo', 'big', 'blockquote', 'caption', 'cite',
    'code', 'dd,' 'del', 'div', 'dfn', 'dl', 'dt', 'em', 'h1', 'h2', 'h3', 'h4',
    'h5', 'h6', 'ins', 'kbd', 'li', 'ol', 'p', 'pre', 'q', 'samp', 'small',
    'span', 'strong', 'sub', 'sup', 'tt', 'ul', 'var',
])

BLOCK_TAGS = set([
    'blockquote', 'div', 'dl', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'ol', 'p',
    'pre', 'table', 'ul',
])

DROP_TAGS = set(['b', 'u', 'i', 'html'])

VALID_ATTRIBS = set([
    'dir', 'class', 'href', 'id', 'lang', 'xml:lang', 'title', 'colspan', 'rowspan',
    'src', 'width', 'height',
])

VALID_URI_SCHEMES = set([
    'http', 'https', 'tel', 'mailto', 'ftp', 'sip', 'telnet', 'xmpp'
])

class HtmlSanitiser(object):
    def __init__(self, html, id_prefix='s', header_offset=0):
        self.html, self.id_prefix = html, id_prefix
        self.header_offset = header_offset
        self.seen_ids = set()

    def get_sanitised(self):
        return self.sanitise_html(self.html)

    def sanitise_html(self, html):
        html = (u"<html>%s</html>" % html).encode('utf8')
        html = etree.parse(StringIO(html), parser=etree.HTMLParser())

        self.sanitise_node(html)
        self.encapsulate_text_nodes(html)

        return ET.tostring(html)[6:-7]

    def encapsulate_text_nodes(self, html):
    
        html[0:0] = [Element('p')]
        html[0].text, html.text = html.text, None
        
        i = 1
        while i < len(html):
            node = html[i]
            
            if node.tag in BLOCK_TAGS:
                if not (html[i-1].text or len(html[i-1])):
                    html[i-1:i], i = [], i-1
                html[i+1:i+1] = [Element('p')]
                html[i+1].text, node.tail = node.tail, None
                
                i += 2 
            else:
                html[i-1].append(node)
                html[i:i+1] = []
                
    def sanitise_node(self, node, parents=()):

        node[0:0], i = [Element('start')], 1
        while i < len(node):
            n = node[i]
            if n.tag in DROP_TAGS:
                if node[-1].tail:
                    node[-1].tail += n.text
                else:
                    node[-1].tail = n.text
                node[i:i+1] = n.getchildren()
            elif not n.tag in VALID_TAGS:
                node[i:i+1] = []
            else:
                i += 1

        for attrib in set(node.attrib):
            if not attrib in VALID_ATTRIBS:
                del node.attrib[attrib]
                continue
            method_name = 'attrib_' + attrib
            if hasattr(self, method_name):
                getattr(self, method_name)(node, node.attrib[attrib])

        method_name = 'tag_' + node.tag
        if hasattr(self, method_name):
            getattr(self, method_name)(node)

        for n in node[1:]:
            self.sanitise_node(n, parents=parents+(node,))

        i = 1
        while i < len(node):
            n = node[i]
            if n.tag in REMOVE_IF_EMPTY and len(n) == 0 and n.text == None:
                node[i:i+1] = []
            else:
                i += 1

        if node.text:
            node.text += node[0].tail or ''
        else:
            node.text = node[0].tail or None
        node[0:1] = []

    def attrib_colspan(self, node, value):
        try:
            assert int(value) > 0
        except (ValueError, AssertionError):
            del node.attrib['colspan']

    def attrib_dir(self, node, value):
        if not value in ('ltr', 'rtl'):
            del node.attrib['dir']

    def attrib_href(self, node, value):
        if node.tag != 'a':
            del node.attrib['href']
            return

        if not value.split(':')[0] in VALID_URI_SCHEMES:
            del node.attrib['href']
            return

    def attrib_id(self, node, value):
        while value in self.seen_ids:
            value.append('-')
        self.seen_ids.add(value)
        node.attrib['id'] = '%s-%s' % (self.id_prefix, value)

    def attrib_rowspan(self, node, value):
        try:
            assert int(value) > 0
        except (ValueError, AssertionError):
            del node.attrib['rowspan']

    def tag_a(self, node):
        if not 'href' in node.attrib:
            node.tag = 'span'
        else:
            node.attrib['rel'] = 'nofollow'

    def tag_br(self, node):
        for attrib in set(['dir', 'lang', 'xml:lang']):
            if attrib in node.attrib:
                del node.attrib[attrib]
        node[1:] = []
        node.text = ''
    tag_hr = tag_br
    
    def tag_h1(self, node):
        n = int(node.tag[1]) + self.header_offset
        if n > 6:
            self.tag = None
        else:
            self.tag = 'h%d' % n
    tag_h6 = tag_h5 = tag_h4 = tag_h3 = tag_h2 = tag_h1

def sanitise_html(html):
    hs = HtmlSanitiser(html, id_prefix='s', header_offset=0)
    ret = hs.get_sanitised()
    return ret

