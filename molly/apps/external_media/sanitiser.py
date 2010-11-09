from lxml import etree

from molly.utils.xslt import transform

def sanitise_html(dirty_html, opener=None, device=None):
    html = etree.fromstring("<div>%s</div>" % dirty_html, parser = etree.HTMLParser())
    html = transform(html, 'external_media/html_sanitiser.xslt')
    
    #if True or device:
    #    for element in html.findall(".//img[@externalmedia]"):
    #        print element

    return etree.tostring(html, method='html')[5:-6] # serialize and remove the div tag

if __name__ == '__main__':
    print sanitise_html("""Hello <img src="http://example.com/"><br> <strong>Squ<em style="font-weight:bold" onload="foo()">e</em>ak</strong>""")