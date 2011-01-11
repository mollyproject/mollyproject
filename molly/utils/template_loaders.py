import os.path

from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import BaseLoader
import django.template.loaders.app_directories
import django.template.loaders.filesystem

class MollyDefaultLoader(BaseLoader):
    """
    Always shows the built-in templates as molly_default/...
    """
    
    is_usable = True
    def load_template_source(self, template_name, template_dirs=None):
        template_parts = template_name.split('/')
        if template_parts[0] == 'molly_default':
            template_rest = '/'.join(template_parts[1:])
            try:
                loader = django.template.loaders.app_directories.Loader()
                return loader.load_template_source(template_rest, template_dirs)
            except TemplateDoesNotExist:
                loader = django.template.loaders.filesystem.Loader()
                return loader.load_template_source(
                  template_rest,
                  (os.path.join(os.path.dirname(__file__), '..', 'templates'),))
        else:
            # This isn't a template we care about
            raise TemplateDoesNotExist()