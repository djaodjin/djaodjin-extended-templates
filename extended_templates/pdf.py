# Copyright (c) 2014, Djaodjin Inc.
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

from django.template import Template
from django.template.response import TemplateResponse
from fdfgen import forge_fdf
from xhtml2pdf import pisa


LOGGER = logging.getLogger(__name__)


class PdfTemplateResponse(TemplateResponse):
    """
    Response as PDF content.
    """

    #pylint: disable=too-many-arguments
    def __init__(self, request, template, context=None, content_type=None,
            status=None, mimetype=None, current_app=None):
        super(PdfTemplateResponse, self).__init__(
            request=request, template=template, context=context,
            content_type='application/pdf', status=status, mimetype=mimetype,
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


# The following was derived from code originally posted
# at https://gist.github.com/zyegfryed/918403

class PdfTemplateError(Exception):
    pass


class PdfTemplate(Template):

    def __init__(self, template_string, origin=None, name='<Unknown Template>'):
        super(PdfTemplate, self).__init__(template_string, origin, name)
        self.origin = origin

    def render(self, context):
        context = context.items()
        output, err = self.fill_form(context, self.origin.name)
        if err:
            raise PdfTemplateError(err)
        return output

    @staticmethod
    def fill_form(fields, src, pdftk_bin=None):
        if pdftk_bin is None:
            from django.conf import settings
            assert hasattr(settings, 'PDFTK_BIN'), "PDF generation requires"\
" pdftk (http://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/). Edit your"\
" PDFTK_BIN settings accordingly."
            pdftk_bin = settings.PDFTK_BIN

        fdf_stream = forge_fdf(fdf_data_strings=fields)

        cmd = [
            pdftk_bin,
            src,
            'fill_form',
            '-',
            'output',
            '-',
            'flatten',
        ]
        cmd = ' '.join(cmd)
        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, shell=True)
            return process.communicate(input=fdf_stream)
        except OSError:
            return (None, None)


