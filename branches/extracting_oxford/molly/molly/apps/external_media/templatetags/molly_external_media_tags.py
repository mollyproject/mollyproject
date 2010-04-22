from django import template

from molly.apps.external_media.utils import resize_external_image

register = template.Library()

@register.tag(name='external_image')
def external_image(parser, token):
    args = token.split_contents()
    if not len(args) in (2, 3):
        raise template.TemplateSyntaxError, "%r takes one argument (the image location)" % token.contents.split()[0]
    if len(args) == 3:
        return ExternalImageNode(template.Variable(args[1]), False)
    else:
        return ExternalImageNode(template.Variable(args[1]))

class ExternalImageNode(template.Node):
    """
    Takes the form {% external_image url %} and renders as a URL pointing at
    the given image resized to match the device's max_image_width.
    """

    def __init__(self, url, just_url=True):
        self.url, self.just_url = url, just_url

    def render(self, context):
        url, width = self.url.resolve(context), context['device'].max_image_width

        eis = resize_external_image(url, width)

        if not eis:
            return ''
        elif self.just_url:
            return eis.get_absolute_url()
        else:
            return """<div class="backgrounded-image" style="background-image:url('%s'); height:%dpx"> </div>""" % (eis.get_absolute_url(), eis.height)


