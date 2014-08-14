# Copyright (c) 2014, DjaoDjin inc.
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

import codecs

from django.template import Template, loader
from django.template.loader import find_template, LoaderOrigin

from extended_templates.pdf import PdfTemplate
from extended_templates.eml import EmlTemplate


# The following was derived from code originally posted
# at https://gist.github.com/zyegfryed/918403

def get_template_from_string(source, origin=None, name=None):
    """
    Returns a compiled Template object for the given template code,
    handling template inheritance recursively.
    """
    if name and name.endswith('.eml'):
        return EmlTemplate(source, origin, name)
    if name and name.endswith('.pdf'):
        return PdfTemplate('pdf', origin, name)
    return Template(source, origin, name)


def make_origin(display_name, from_loader, name, dirs):
    # Always return an Origin object, because PdfTemplate need it to render
    # the PDF Form file.
    return LoaderOrigin(display_name, from_loader, name, dirs)


def get_template(template_name):
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
        return (u'', -1)

    if template_name.endswith('.pdf'):
        # HACK: Ignore UnicodeError, due to PDF file read
        codecs.register_error('strict', fake_strict_errors)

    template, origin = find_template(template_name)
    if not hasattr(template, 'render'):
        # template needs to be compiled
        template = get_template_from_string(template, origin, template_name)

    if template_name.endswith('.pdf'):
        # HACK: Ignore UnicodeError, due to PDF file read
        codecs.register_error('strict', codecs.strict_errors)

    return template
