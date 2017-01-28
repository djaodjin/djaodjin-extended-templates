# Copyright (c) 2017, Djaodjin Inc.
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

import warnings

from bs4 import BeautifulSoup
import django
from django.core.mail import EmailMultiAlternatives
from django.template import engines
from django.utils.html import strip_tags
from django.template import TemplateDoesNotExist
from premailer import Premailer

from .. import settings
from ..compat import (BaseEngine, _dirs_undefined, import_string,
    RemovedInDjango110Warning)


def build_absolute_uri(request, location='', site=None):
    if settings.BUILD_ABSOLUTE_URI_CALLABLE:
        return import_string(settings.BUILD_ABSOLUTE_URI_CALLABLE)(
            request, location=location, site=site)
    return request.build_absolute_uri(location=location)


class EmlTemplateError(Exception):
    pass


class EmlEngine(BaseEngine):
    #pylint: disable=no-member

    app_dirname = 'eml'
    template_context_processors = tuple([])

    def __init__(self, params):
        params = params.copy()
        options = params.pop('OPTIONS').copy()
        self.engine = engines[options.get('engine', 'html')]
        super(EmlEngine, self).__init__(params)

    @staticmethod
    def get_templatetag_libraries(custom_libraries):
        """
        Return a collation of template tag libraries from installed
        applications and the supplied custom_libraries argument.
        """
        #pylint: disable=no-name-in-module,import-error
        from django.template.backends.django import get_installed_libraries
        libraries = get_installed_libraries()
        libraries.update(custom_libraries)
        return libraries

    def find_template(self, template_name, dirs=None, skip=None):
        tried = []
        for loader in self.template_loaders:
            if hasattr(loader, 'get_contents'):
                # From Django 1.9, this is the code that should be executed.
                try:
                    template = Template(loader.get_template(
                        template_name, template_dirs=dirs, skip=skip,
                    ))
                    return template, template.origin
                except TemplateDoesNotExist as err:
                    tried.extend(err.tried)
            else:
                # This code is there to support Django 1.8 only.
                from ..compat import DjangoTemplate
                try:
                    source, template_path = loader.load_template_source(
                        template_name, template_dirs=dirs)
                    origin = self.make_origin(
                        template_path, loader.load_template_source,
                        template_name, dirs)
                    template = Template(
                        DjangoTemplate(source, origin, template_path, self))
                    return template, template.origin
                except TemplateDoesNotExist:
                    pass
        raise TemplateDoesNotExist(template_name, tried=tried)

    def from_string(self, template_code):
        return Template(self.engine.from_string(template_code), engine=self)

    def get_template(self, template_name, dirs=_dirs_undefined):
        #pylint:disable=arguments-differ
        if template_name and template_name.endswith('.eml'):
            if dirs is _dirs_undefined:
                return Template(self.engine.get_template(
                    template_name), engine=self)
            else:
                if django.VERSION[0] >= 1 and django.VERSION[1] >= 8:
                    warnings.warn(
                        "The dirs argument of get_template is deprecated.",
                        RemovedInDjango110Warning, stacklevel=2)
                return Template(self.engine.get_template(
                    template_name, dirs=dirs), engine=self)
        raise TemplateDoesNotExist(template_name)


class Template(object):
    """
    Sends an email to a list of recipients (i.e. email addresses).
    """

    def __init__(self, template, engine=None):
        self.engine = engine
        self.template = template
        self.origin = template.origin
        if self.origin:
            self.name = self.origin.name

    def render(self, context=None, request=None):
        return self.template.render(context=context, request=request)

    #pylint: disable=invalid-name,too-many-arguments
    def _send(self, recipients, context, from_email=None, bcc=None, cc=None,
              reply_to=None, attachments=None, fail_silently=False):
        #pylint: disable=too-many-locals
        if reply_to:
            headers = {'Reply-To': reply_to}
        else:
            headers = None

        subject = None
        plain_content = None
        request = getattr(context, 'request', context.get('request', None))

        soup = BeautifulSoup(self.render(
            context=context, request=request), 'html.parser')
        for lnk in soup.find_all('a'):
            href = lnk.get('href')
            if href and href.startswith('/'):
                lnk['href'] = build_absolute_uri(request, href)
        html_content = soup.prettify()
        subject = soup.find("title").contents[0].strip()

        # Create the email, attach the HTML version.
        if not subject:
            raise EmlTemplateError(
                "Template %s is missing a subject." % self.origin.name)
        if not plain_content:
            # Defaults to content stripped of html tags
            if not html_content:
                raise EmlTemplateError(
                    "Template %s does not contain PLAIN nor HTML content."
                    % self.origin.name)
            plain_content = strip_tags(html_content)
        # XXX implement inline attachments,
        #     reference: https://djangosnippets.org/snippets/3001/
        msg = EmailMultiAlternatives(
            subject, plain_content, from_email, recipients, bcc=bcc, cc=cc,
            attachments=attachments, headers=headers)
        if html_content:
            html_content = Premailer(
                html_content,
                include_star_selectors=True).transform()
            msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=fail_silently)

    #pylint: disable=invalid-name,too-many-arguments
    def send(self, recipients, context,
             from_email=None, bcc=None, cc=None, reply_to=None,
             attachments=None, fail_silently=False):
        #pylint: disable=no-member
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL

        if hasattr(context, 'template') and context.template is None:
            with context.bind_template(self):
                context.template_name = self.name
                return self._send(recipients, context, from_email=from_email,
                    bcc=bcc, cc=cc, reply_to=reply_to, attachments=attachments,
                    fail_silently=fail_silently)
        else:
            return self._send(recipients, context, from_email=from_email,
                bcc=bcc, cc=cc, reply_to=reply_to, attachments=attachments,
                fail_silently=fail_silently)
