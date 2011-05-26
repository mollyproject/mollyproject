from django.utils.translation import get_language
from django.db.models import Model
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

try:
    from django.utils.translation import override
except ImportError:
    from django.utils.translation import activate, deactivate
    class override(object):
        def __init__(self, language, deactivate=False):
            self.language = language
            self.deactivate = deactivate
            self.old_language = get_language()
        
        def __enter__(self):
            activate(self.language)
        
        def __exit__(self, exc_type, exc_value, traceback):
            if self.deactivate:
                deactivate()
            else:
                activate(self.old_language)


def name_in_language(obj, field):
    try:
        return getattr(obj.names.get(language_code=get_language()), field)
    except ObjectDoesNotExist:
        try:
            return getattr(obj.names.get(language_code=settings.LANGUAGE_CODE), field)
        except ObjectDoesNotExist:
            if '-' in settings.LANGUAGE_CODE:
                return getattr(obj.names.get(language_code=settings.LANGUAGE_CODE.split('-')[0]), field)
            else:
                raise