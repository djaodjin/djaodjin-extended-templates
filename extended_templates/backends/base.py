# Copyright (c) 2025, Djaodjin Inc.
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

from __future__ import unicode_literals

import codecs, logging, warnings
from importlib import import_module

import django
from django.template import Template, loader
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import select_template

from .. import settings
from ..compat import _dirs_undefined, RemovedInDjango110Warning, six
from .pdf import Template as PdfTemplate
from .eml import Template as EmlTemplate


LOGGER = logging.getLogger(__name__)


def make_origin(display_name, from_loader, name, dirs):
    # Always return an Origin object, because PdfTemplate need it to render
    # the PDF Form file.
    # It seems that `LoaderOrigin` is no longer present in the Django project
    # since version 2.2 ...
    return loader.LoaderOrigin(display_name, from_loader, name, dirs)


def get_email_backend(connection=None):
    return _load_backend(settings.EMAILER_BACKEND)(connection=connection)


def get_template_from_string(source, origin=None, name=None):
    """
    Returns a compiled Template object for the given template code,
    handling template inheritance recursively.
    """
    # This function is deprecated in Django 1.8+
    #pylint:disable=too-many-function-args
    if name and name.endswith('.eml'):
        return EmlTemplate(source, origin, name)
    if name and name.endswith('.pdf'):
        return PdfTemplate('pdf', origin, name)
    return Template(source, origin, name)


def get_template(template_name, dirs=_dirs_undefined):
    """
    Returns a compiled Template object for the given template name,
    handling template inheritance recursively.
    """
    # Implementation Note:
    # If we do this earlier (i.e. when the module is imported), there
    # is a chance our hook gets overwritten somewhere depending on the
    # order in which the modules are imported.
    loader.get_template_from_string = get_template_from_string
    loader.make_origin = make_origin

    def fake_strict_errors(exception): #pylint: disable=unused-argument
        return ("", -1)

    if template_name.endswith('.pdf'):
        # HACK: Ignore UnicodeError, due to PDF file read
        codecs.register_error('strict', fake_strict_errors)

    if dirs is _dirs_undefined:
        template = loader.get_template(template_name)
    else:
        if django.VERSION[0] >= 1 and django.VERSION[1] >= 8:
            warnings.warn(
                "The dirs argument of get_template is deprecated.",
                RemovedInDjango110Warning, stacklevel=2)
        #pylint:disable=unexpected-keyword-arg
        template = loader.get_template(template_name, dirs=dirs)

    if template_name.endswith('.pdf'):
        # HACK: Ignore UnicodeError, due to PDF file read
        codecs.register_error('strict', codecs.strict_errors)

    return template


def _load_backend(path):
    dot_pos = path.rfind('.')
    module, attr = path[:dot_pos], path[dot_pos + 1:]
    try:
        mod = import_module(module)
    except ImportError as err:
        raise ImproperlyConfigured('Error importing emailer backend %s: "%s"'
            % (path, err))
    except ValueError:
        raise ImproperlyConfigured('Error importing emailer backend. '\
' Is EMAILER_BACKEND a correctly defined list or tuple?')
    try:
        cls = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" '\
' emailer backend' % (module, attr))
    return cls


class TemplateEmailBackend(object):

    def __init__(self, connection=None):
        self.connection = connection

    #pylint: disable=invalid-name,too-many-arguments
    def send(self, recipients, template, context=None,
             from_email=None, bcc=None, cc=None, reply_to=None,
             attachments=None, fail_silently=False):
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL

        if isinstance(template, (list, tuple)):
            tmpl = select_template(template)
        elif isinstance(template, six.string_types):
            tmpl = get_template(template)
        else:
            tmpl = template
        tmpl.send(recipients, context,
            from_email=from_email, bcc=bcc, cc=cc, reply_to=reply_to,
            attachments=attachments, connection=self.connection,
            fail_silently=fail_silently)
