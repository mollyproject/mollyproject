from StringIO import StringIO
from xml.sax.saxutils import escape
import ElementSoup as ES

VALID_TAGS = set([
    'a', 'abbr', 'address', 'bdo', 'big', 'blockquote', 'br', 'caption', 'cite',
    'code', 'col', 'colgroup', 'dd', 'del', 'div', 'dfn', 'dl', 'dt', 'em',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'img', 'ins', 'kbd', 'li', 'ol', 'p', 'pre',
    'q', 'samp', 'small', 'span', 'strong', 'sub', 'sup', 'table', 'tbody',
    'td', 'tfoot', 'th', 'thead', 'tr', 'tt', 'ul', 'var',
])

DROP_TAGS = set(['b', 'u', 'i', 'html'])

VALID_ATTRIBS = set([
    'dir', 'class', 'href', 'id', 'lang', 'xml:lang', 'title', 'colspan', 'rowspan',
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
        html = ES.parse(StringIO(html), encoding='utf8')

        return self.sanitise_node(html)

    def sanitise_node(self, node):
        if node.tag in DROP_TAGS:
            ret = [node.text or '']
            for n in node:
                ret.append(self.sanitise_node(n))
                ret.append(n.tail or '')
            return ''.join(ret)

        if not node.tag in VALID_TAGS:
            return ''

        for attrib in set(node.attrib):
            if not attrib in VALID_ATTRIBS:
                del node.attribs[attrib]
                continue
            method_name = 'attrib_' + attrib
            if hasattr(self, method_name):
                getattr(self, method_name)(node, node.attrib[attrib])

        method_name = 'tag_' + node.tag
        if hasattr(self, method_name):
            getattr(self, method_name)(node)

        if not node.tag:
            return ''

        if len(node.attrib):
            ret = ['<%s %s>' % (node.tag, ' '.join(('%s="%s"' % (k, escape(v)) for (k, v) in node.attrib.items())))]
        else:
            ret = ['<%s>' % node.tag]
        ret.append(node.text or '')
        for n in node:
            ret.append(self.sanitise_node(n))
            ret.append(n.tail or '')
        ret.append('</%s>' % node.tag)
        if len(ret) == 3 and ret[1] == '':
            ret = [ret[0][:-1]+'/>']
        return ''.join(ret) 

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
        self.attrib['id'] = '%s-%s' % (self.id_prefix, value)

    def attrib_rowspan(self, node, value):
        try:
            assert int(value) > 0
        except (ValueError, AssertionError):
            del node.attrib['rowspan']

    def tag_a(self, node):
        if not 'href' in node.attrib:
            node.tag = 'span'

    def tag_br(self, node):
        for attrib in set(['dir', 'lang', 'xml:lang']):
            if attrib in node.attrib:
                del node.attrib[attrib]
        node[:] = []
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

if __name__ == '__main__':
    hs = HtmlSanitiser('<a href="foo">Hello<script>foo</script></p>')
    print hs.get_sanitised()