# Copyright (c) 2016, Djaodjin Inc.
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

import logging, subprocess, StringIO

from django.template import TemplateDoesNotExist, Template as BaseTemplate
from django.template.response import TemplateResponse
from xhtml2pdf import pisa

from .. import settings
from ..compat import BaseEngine, _dirs_undefined


LOGGER = logging.getLogger(__name__)


class PdfTemplateResponse(TemplateResponse):
    """
    Response as PDF content.
    """

    #pylint:disable=too-many-arguments
    def __init__(self, request, template, context=None, content_type=None,
                 status=None, **kwargs):
        # Django 1.9 added (charset=None, using=None) to the prototype.
        # Django 1.10 removed (current_app=None)  to the prototype.
        # We donot declare them explicitely but through **kwargs instead
        # so that our prototype is compatible with from Django 1.7
        # through to Django 1.10.
        super(PdfTemplateResponse, self).__init__(request, template,
            context=context, content_type='application/pdf', status=status,
            **kwargs)

    @property
    def rendered_content(self):
        """
        Converts the HTML content generated from the template
        as a Pdf document on the fly.
        """
        content = super(PdfTemplateResponse, self).rendered_content
        cstr = StringIO.StringIO()
        pdf = pisa.pisaDocument(
            StringIO.StringIO(content.encode('UTF-8')), cstr, encoding='UTF-8')
        if pdf.err:
            raise PdfTemplateError(pdf.err)
        return cstr.getvalue()


class PdfTemplateError(Exception):
    pass


class PdfEngine(BaseEngine):
    #pylint: disable=no-member

    app_dirname = 'pdf'

    def __init__(self, params):
        self.name = params.get('NAME')
        dirs = list(params.get('DIRS', []))
        app_dirs = bool(params.get('APP_DIRS', False))
        options = params.get('OPTIONS', {})
        super(PdfEngine, self).__init__(dirs=dirs, app_dirs=app_dirs, **options)

    def find_template(self, template_name, dirs=None, skip=None):
        tried = []
        for loader in self.template_loaders:
            if hasattr(loader, 'get_contents'):
                # From Django 1.9, this is the code that should be executed.
                for origin in loader.get_template_sources(
                        template_name, template_dirs=dirs):
                    if skip is not None and origin in skip:
                        tried.append((origin, 'Skipped'))
                        continue
                    try:
                        contents = loader.get_contents(origin)
                    except TemplateDoesNotExist:
                        tried.append((origin, 'Source does not exist'))
                        continue
                    else:
                        template = Template(
                            contents, origin, origin.template_name, self)
                        return template, template.origin
            else:
                # This code is there to support Django 1.8 only.
                try:
                    source, template_path = loader.load_template_source(
                        template_name, template_dirs=dirs)
                    origin = self.make_origin(
                        template_path, loader.load_template_source,
                        template_name, dirs)
                    template = Template(source, origin, template_path, self)
                    return template, template.origin
                except TemplateDoesNotExist:
                    pass
        raise TemplateDoesNotExist(template_name, tried=tried)

    def get_template(self, template_name, dirs=_dirs_undefined):
        if template_name and template_name.endswith('.pdf'):
            return super(PdfEngine, self).get_template(template_name, dirs=dirs)
        raise TemplateDoesNotExist(template_name)


class Template(BaseTemplate):

    def __init__(self, template_string, origin=None, name=None, engine=None):
        if engine is not None:
            kwargs = {'engine': engine}
        else:
            kwargs = {}
        super(Template, self).__init__(template_string, origin=origin,
            name=name, **kwargs)
        self.origin = origin

    def render(self, context):
        if self.origin:
            template_path = self.origin.name
        else:
            template_path = self.name
        output, err = self.fill_form(context, template_path)
        if err:
            raise PdfTemplateError(err)
        return output

    @staticmethod
    def fill_form(fields, src, pdf_flatform_bin=None):
        if pdf_flatform_bin is None:
            assert hasattr(settings, 'PDF_FLATFORM_BIN'), "PDF generation "\
" requires podofo-flatform (https://github.com/djaodjin/"\
"djaodjin-extended-templates/src/podofo-flatform.cc). Edit your"\
" PDF_FLATFORM_BIN settings accordingly."
            pdf_flatform_bin = settings.PDF_FLATFORM_BIN

        cmd = [unicode(pdf_flatform_bin)]
        for key, value in fields.iteritems():
            if len(str(value)) > 0:
                # We don't want to end-up with ``--fill key=``
                cmd += [u'--fill', (u'%s=%s' % (key, value))]
        cmd += [unicode(src), u'-']

        cmdline = cmd[0]
        for param in cmd[1:]:
            try:
                key, value = param.split('=')
                if any(char in str(value) for char in [' ', ';']):
                    value = u'"%s"' % value
                cmdline += u" %s=%s" % (key, value)
            except ValueError:
                cmdline += u" " + param
        LOGGER.info((u'RUN: %s' % cmdline).encode('utf-8'))

        return subprocess.check_output(cmd), None
