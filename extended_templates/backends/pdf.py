# Copyright (c) 2015, Djaodjin Inc.
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

from django.conf import settings as django_settings
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

    #pylint: disable=too-many-arguments
    def __init__(self, request, template, context=None, content_type=None,
            status=None, current_app=None):
        super(PdfTemplateResponse, self).__init__(
            request=request, template=template, context=context,
            content_type='application/pdf', status=status,
            current_app=current_app)

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
        options = params.pop('OPTIONS').copy()
        options.setdefault('debug', django_settings.DEBUG)
        options.setdefault('file_charset', django_settings.FILE_CHARSET)
        super(PdfEngine, self).__init__(params)
        self.loaders = [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader']

    def find_template(self, template_name, dirs=None):
        for loader in self.template_loaders:
            try:
                source, display_name = loader.load_template_source(
                    template_name, template_dirs=dirs)
                origin = self.make_origin(
                    display_name, loader.load_template_source,
                template_name, dirs)
                template = Template(source, origin, template_name, self)
                return template, None
            except TemplateDoesNotExist:
                pass
        raise TemplateDoesNotExist(template_name)

    def get_template(self, template_name, dirs=_dirs_undefined):
        if template_name and template_name.endswith('.pdf'):
            return super(PdfEngine, self).get_template(template_name, dirs=dirs)
        raise TemplateDoesNotExist()


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
        output, err = self.fill_form(context, self.origin.name)
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

        cmd = [pdf_flatform_bin]
        for key, value in fields.iteritems():
            cmd += ['--fill', str('%s=%s' % (key, value))]
        cmd += [src, '-']

        LOGGER.info('RUN: %s', ' '.join(cmd))
        print "XXX RUN: %s" % str(cmd)
        return subprocess.check_output(cmd), None

#        cmd = ' '.join(cmd)
#        process = subprocess.Popen(cmd, stdin=subprocess.PIPE,
#                                   stdout=subprocess.PIPE, shell=True)
#        stdout, stderr = process.communicate(input=fdf_stream)
#        process.wait()
#        if process.returncode != 0:
#            LOGGER.exception("Unable to generate PDF: %s", cmd)
#        return stdout, stderr


