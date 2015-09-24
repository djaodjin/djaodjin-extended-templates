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

from bs4 import BeautifulSoup
from django.conf import settings as django_settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.template import RequestContext, Context
from django.template.loader_tags import BlockNode, ExtendsNode
from django.utils.html import strip_tags
from django.template import TemplateDoesNotExist, Template as BaseTemplate

from premailer import Premailer

from .. import settings
from ..compat import BaseEngine, _dirs_undefined


class EmlTemplateError(Exception):
    pass


class EmlEngine(BaseEngine):
    #pylint: disable=no-member

    app_dirname = 'eml'

    def __init__(self, params):
        options = params.pop('OPTIONS').copy()
        options.setdefault('debug', django_settings.DEBUG)
        options.setdefault('file_charset', django_settings.FILE_CHARSET)
        super(EmlEngine, self).__init__(params)
        self.engine = BaseEngine(self.dirs, self.app_dirs, **options)

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
        if template_name and template_name.endswith('.eml'):
            return super(EmlEngine, self).get_template(template_name, dirs=dirs)
        raise TemplateDoesNotExist()


class Template(BaseTemplate):
    """
    Sends an email to a list of recipients (i.e. email addresses).
    """

    def __init__(self, template_string, origin=None, name=None, engine=None):
        if engine is not None:
            kwargs = {'engine': engine}
        else:
            kwargs = {}
        super(Template, self).__init__(template_string, origin=origin,
            name=name, **kwargs)
        self.origin = origin

    #pylint: disable=invalid-name,too-many-arguments
    def send(self, recipients, context,
             from_email=None, bcc=None, cc=None, reply_to=None,
             attachments=None):
        #pylint: disable=too-many-locals
        if reply_to:
            headers = {'Reply-To': reply_to}
        else:
            headers = None
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL
        subject = None
        html_content = None
        plain_content = None
        context = RequestContext(None, context)
        extend = None
        nodes = self

        # Check if need to extend from base
        if isinstance(self.nodelist[0], ExtendsNode):
            extend = self.nodelist[0]
            nodes = self.nodelist[0].nodelist

        for node in nodes:
            if isinstance(node, BlockNode):
                if node.name == 'subject':
                    # Email subject *must not* contain newlines
                    subject = ''.join(node.render(context).splitlines())
                elif node.name == 'html_content':
                    html_content = node.render(context)
                    if extend:
                        soup = BeautifulSoup(html_content, 'html.parser')
                    else:
                        soup = BeautifulSoup(html_content, 'lxml')

                    for lnk in soup.find_all('a'):
                        href = lnk.get('href')
                        if href and href.startswith('/'):
                            lnk['href'] = 'http://%s%s' % (
                                Site.objects.get_current(), href)
                    if extend:
                        html_base_content = extend.render(context)
                        soup_base = BeautifulSoup(html_base_content, 'lxml')
                        content_section = soup_base.find(id='content')
                        content_section.insert(0, soup)
                        html_content = soup_base.prettify()
                    else:
                        html_content = soup.prettify()
                elif node.name == 'plain_content':
                    plain_content = node.render(context)

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
        msg.send(fail_silently=False)

