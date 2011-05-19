from logging import getLogger

from django import template

from molly.external_media import resize_external_image

register = template.Library()

logger = getLogger(__name__)

@register.tag(name='external_image')
def external_image(parser, token):
    args = token.split_contents()
    if not len(args) in (2, 3, 4):
        raise template.TemplateSyntaxError, "%r takes one argument (the image location)" % token.contents.split()[0]

    try:
        max_width = template.Variable(args[2])
    except (ValueError, IndexError):
        max_width = None
    if 'asdiv' in args:
        return ExternalImageNode(template.Variable(args[1]), max_width, False)
    else:
        return ExternalImageNode(template.Variable(args[1]), max_width)


class ExternalImageNode(template.Node):
    """
    Takes the form {% external_image url %} and renders as a URL pointing at
    the given image resized to match the device's max_image_width.
    """

    def __init__(self, url, max_width, just_url=True):
        self.url, self.max_width, self.just_url = url, max_width, just_url

    def render(self, context):
        try:
            width = int(self.max_width.resolve(context))
        except Exception:
            width = float('inf')

        url, width = self.url.resolve(context), min(width, context['device'].max_image_width)
        
        try:
            eis = resize_external_image(url, width)
        except IOError:
            logger.warn('Resizing external image failed', exc_info=True)
            eis = None

        if self.just_url:
            return eis.get_absolute_url() if eis != None else url
        elif eis is None:
            return """<div class="backgrounded-image" style="background-image:url('%s');"> </div>""" % (eis.get_absolute_url() if eis != None else url)
        else:
            return """<div class="backgrounded-image" style="background-image:url('%s'); height:%dpx"> </div>""" % (eis.get_absolute_url(), eis.height)
