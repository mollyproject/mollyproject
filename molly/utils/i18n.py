from copy import copy

from django.utils.translation import get_language
from django.db.models import Model
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.views.i18n import set_language
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

from molly.utils.views import BaseView

def languages_to_try():
    languages = [get_language()]
    if '-' in languages[0]:
        languages.append(languages[0].split('-')[0])
    languages.append(settings.LANGUAGE_CODE)
    if '-' in settings.LANGUAGE_CODE:
        languages.append(settings.LANGUAGE_CODE.split('-')[0])
    return languages
    

def name_in_language(obj, field, default=None):
    """
    Assuming the object follows the Molly pattern for i18n data (related manager
    called names, and the related object has a language_code field), then get
    the i18n'd version of 'field' in the user's current language.
    """
    
    for language_code in languages_to_try():
        try:
            return getattr(obj.names.get(language_code=language_code), field)
        except ObjectDoesNotExist:
            continue
    return None


def set_name_in_language(obj, lang, **fields):
    """
    Assuming the object follows the Molly pattern for i18n data (related manager
    called names, and the related object has a language_code field), then set
    name/language pair to 'field'.
    """
    
    names = obj.names.filter(language_code=lang)
    if names.count() == 0:
        obj.names.create(language_code=lang, **fields)
    else:
        name = names[0]
        for k, v in fields.items():
            setattr(name, k, v)
        name.save()


class SetLanguageView(BaseView):

    def handle_GET(self, request, context):
        return self.render(request, context, 'i18n/index')
    
    def handle_POST(self, request, context):
        if hasattr(request, 'session'):
            # MOLLY-177: Force using cookies to set language
            session = request.session
            del request.session
            ret = set_language(request)
            request.session = session
            return ret
        
        else:
            
            # Do Django's built in language setter
            return set_language(request)


# TODO: When Molly moves to Django 1.4, this can be removed

"""
Below here contains backports from newer versions of Django, licensed under the
BSD license below:

Copyright (c) Django Software Foundation and individual contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, 
       this list of conditions and the following disclaimer.
    
    2. Redistributions in binary form must reproduce the above copyright 
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of Django nor the names of its contributors may be used
       to endorse or promote products derived from this software without
       specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

try:
    from django.utils.translation import override
except ImportError:
    from django.utils.translation import activate, deactivate
    
    # Backported from Django
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

from django.views.i18n import (LibHead, LibFoot, LibFormatHead, LibFormatFoot,
                               SimplePlural, InterPolate, PluralIdx)
import os
import gettext as gettext_module
from django import http
from django.utils import importlib
from django.utils.translation import check_for_language, activate, to_locale, get_language
from django.utils.encoding import smart_unicode
from django.utils.text import javascript_quote
from django.utils.formats import get_format_modules, get_format
from django.views.i18n import get_formats

def javascript_catalog(request, domain='djangojs', packages=None):
    """
    Returns the selected language catalog as a javascript library.

    Receives the list of packages to check for translations in the
    packages parameter either from an infodict or as a +-delimited
    string from the request. Default is 'django.conf'.

    Additionally you can override the gettext domain for this view,
    but usually you don't want to do that, as JavaScript messages
    go to the djangojs domain. But this might be needed if you
    deliver your JavaScript source from Django templates.
    """
    if request.GET:
        if 'language' in request.GET:
            #if check_for_language(request.GET['language']):
            activate(request.GET['language'])
    if packages is None:
        packages = ['django.conf']
    if isinstance(packages, basestring):
        packages = packages.split('+')
    packages = [p for p in packages if p == 'django.conf' or p in settings.INSTALLED_APPS]
    default_locale = to_locale(settings.LANGUAGE_CODE)
    locale = to_locale(get_language())
    t = {}
    paths = []
    en_selected = locale.startswith('en')
    en_catalog_missing = True
    # paths of requested packages
    for package in packages:
        p = importlib.import_module(package)
        path = os.path.join(os.path.dirname(p.__file__), 'locale')
        paths.append(path)
    # add the filesystem paths listed in the LOCALE_PATHS setting
    paths.extend(list(reversed(settings.LOCALE_PATHS)))
    # first load all english languages files for defaults
    for path in paths:
        try:
            catalog = gettext_module.translation(domain, path, ['en'])
            t.update(catalog._catalog)
        except IOError:
            pass
        else:
            # 'en' is the selected language and at least one of the packages
            # listed in `packages` has an 'en' catalog
            if en_selected:
                en_catalog_missing = False
    # next load the settings.LANGUAGE_CODE translations if it isn't english
    if default_locale != 'en':
        for path in paths:
            try:
                catalog = gettext_module.translation(domain, path, [default_locale])
            except IOError:
                catalog = None
            if catalog is not None:
                t.update(catalog._catalog)
    # last load the currently selected language, if it isn't identical to the default.
    if locale != default_locale:
        # If the currently selected language is English but it doesn't have a
        # translation catalog (presumably due to being the language translated
        # from) then a wrong language catalog might have been loaded in the
        # previous step. It needs to be discarded.
        if en_selected and en_catalog_missing:
            t = {}
        else:
            locale_t = {}
            for path in paths:
                try:
                    catalog = gettext_module.translation(domain, path, [locale])
                except IOError:
                    catalog = None
                if catalog is not None:
                    locale_t.update(catalog._catalog)
            if locale_t:
                t = locale_t
    src = [LibHead]
    plural = None
    if '' in t:
        for l in t[''].split('\n'):
            if l.startswith('Plural-Forms:'):
                plural = l.split(':',1)[1].strip()
    if plural is not None:
        # this should actually be a compiled function of a typical plural-form:
        # Plural-Forms: nplurals=3; plural=n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2;
        plural = [el.strip() for el in plural.split(';') if el.strip().startswith('plural=')][0].split('=',1)[1]
        src.append(PluralIdx % plural)
    else:
        src.append(SimplePlural)
    csrc = []
    pdict = {}
    for k, v in t.items():
        if k == '':
            continue
        if isinstance(k, basestring):
            csrc.append("catalog['%s'] = '%s';\n" % (javascript_quote(k), javascript_quote(v)))
        elif isinstance(k, tuple):
            if k[0] not in pdict:
                pdict[k[0]] = k[1]
            else:
                pdict[k[0]] = max(k[1], pdict[k[0]])
            csrc.append("catalog['%s'][%d] = '%s';\n" % (javascript_quote(k[0]), k[1], javascript_quote(v)))
        else:
            raise TypeError(k)
    csrc.sort()
    for k, v in pdict.items():
        src.append("catalog['%s'] = [%s];\n" % (javascript_quote(k), ','.join(["''"]*(v+1))))
    src.extend(csrc)
    src.append("""var language_code = '%s'""" % locale)
    src.append(LibFoot)
    src.append(InterPolate)
    src.append(LibFormatHead)
    src.append(get_formats())
    src.append(LibFormatFoot)
    src = ''.join(src)
    return http.HttpResponse(src, 'text/javascript')
