# Copyright (c) 2022, Djaodjin Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#pylint:disable=unused-import,no-name-in-module,import-outside-toplevel
#pylint:disable=no-name-in-module,import-error
from functools import WRAPPER_ASSIGNMENTS
import re

import six
from six.moves.urllib.parse import urljoin, urlparse, urlsplit, urlunparse
from django.core.exceptions import ImproperlyConfigured

try:
    from django.utils.decorators import available_attrs
except ImportError: # django < 3.0
    def available_attrs(func):      #pylint:disable=unused-argument
        return WRAPPER_ASSIGNMENTS


try:
    from django.template.backends.base import BaseEngine
except ImportError: # django < 1.8
    from django.template import Template as DjangoTemplate
    class BaseEngine(object):
        def __init__(self, params):
            params = params.copy()
            self.name = params.pop('NAME')
            self.dirs = list(params.pop('DIRS'))
            self.app_dirs = bool(params.pop('APP_DIRS'))
            if params:
                raise ImproperlyConfigured(
                    "Unknown parameters: {}".format(", ".join(params)))


try:
    from django.template.engine import _dirs_undefined
except ImportError: # django < 1.8
    _dirs_undefined = object()

try:
    from django.utils.deprecation import RemovedInDjango110Warning
except ImportError: # django < 1.8
    class RemovedInDjango110Warning(PendingDeprecationWarning):
        pass

try:
    from django.utils.encoding import python_2_unicode_compatible
except ImportError: # django < 3.0
    python_2_unicode_compatible = six.python_2_unicode_compatible

from django import VERSION as DJANGO_VERSION
from django.conf import settings as django_settings
from django.template import RequestContext

try:
    from django.templatetags.static import do_static
except ImportError: # django < 2.1
    from django.contrib.staticfiles.templatetags import do_static

try:
    from django.template.context_processors import csrf
except ImportError: # django < 1.8
    from django.core.context_processors import csrf #pylint:disable=import-error

try:
    from django.template.exceptions import TemplateDoesNotExist
except ImportError:
    from django.template.base import TemplateDoesNotExist

try:
    from django.urls import NoReverseMatch, reverse, reverse_lazy
except ImportError: # <= Django 1.10, Python<3.6
    from django.core.urlresolvers import NoReverseMatch, reverse, reverse_lazy
except ModuleNotFoundError: #pylint:disable=undefined-variable,bad-except-order
    # <= Django 1.10, Python>=3.6
    from django.core.urlresolvers import NoReverseMatch, reverse, reverse_lazy

try:
    from django.urls import include, path, re_path
except ImportError: # <= Django 2.0, Python<3.6
    from django.conf.urls import include, url as re_path

    def path(route, view, kwargs=None, name=None):
        re_route = re.sub(
            r'<slug:([a-z\_]+)>', r'(?P<\1>[a-zA-Z0-9_\-\+\.]+)', route)
        return re_path(re_route, view, kwargs=kwargs, name=name)

try:
    if six.PY3:
        from django.utils.encoding import force_str
    else:
        from django.utils.encoding import force_text as force_str
except ImportError: # django < 3.0
    from django.utils.encoding import force_text as force_str


try:
    from django.utils.module_loading import import_string
except ImportError: # django < 1.7
    from django.utils.module_loading import import_by_path as import_string


try:
    from django.utils.translation import gettext_lazy
except ImportError: # django < 3.0
    from django.utils.translation import ugettext_lazy as gettext_lazy


def get_loaders():
    loaders = []
    try:
        from django.template.loader import _engine_list
        engines = _engine_list()
        for engine in engines:
            try:
                loaders += engine.engine.template_loaders
            except AttributeError:
                pass
            try:
                loaders += engine.template_loaders
            except AttributeError:
                pass

    except ImportError:# django < 1.8
        from django.template.loader import find_template_loader
        for loader_name in django_settings.TEMPLATE_LOADERS:
            template_loader = find_template_loader(loader_name)
            if template_loader is not None:
                loaders.append(template_loader)
    return loaders


def render_template(template, context, request):
    """
    In Django 1.7 django.template.Template.render(self, context)
    In Django 1.8 django.template.backends.django.Template.render(
        self, context=None, request=None)
    """
    if DJANGO_VERSION[0] == 1 and DJANGO_VERSION[1] < 8:
        context = RequestContext(request, context)
        return template.render(context)
    return template.render(context, request)


try:
    from django.template.base import DebugLexer
except ImportError: # django < 1.8
    from django.template.debug import DebugLexer as BaseDebugLexer

    class DebugLexer(BaseDebugLexer):

        def __init__(self, template_string):
            super(DebugLexer, self).__init__(template_string, origin=None)


try:
    from django.template.base import TokenType
except ImportError: # django < 2.1
    from django.template.base import (TOKEN_TEXT, TOKEN_VAR, TOKEN_BLOCK,
        TOKEN_COMMENT)
    class TokenType(object):
        TEXT = TOKEN_TEXT
        VAR = TOKEN_VAR
        BLOCK = TOKEN_BLOCK
        COMMENT = TOKEN_COMMENT


def get_html_engine():
    try:
        from django.template import engines
        from django.template.utils import InvalidTemplateEngineError
        try:
            return engines['html'], None, None
        except InvalidTemplateEngineError:
            engine = engines['django'].engine
            return engine, engine.template_libraries, engine.template_builtins
    except ImportError: # django < 1.8
        return DjangoTemplate()


def is_authenticated(request):
    if callable(request.user.is_authenticated):
        return request.user.is_authenticated()
    return request.user.is_authenticated


try:
    from django.core.files.storage import storages # Added in Django 4.2
    def get_storage_class():
        return import_string(storages.backends['default']['BACKEND'])
except ImportError:
    from django.core.files.storage import get_storage_class # Removed in Django 5.0
