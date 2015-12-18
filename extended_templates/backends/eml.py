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
from django.template import Context, RequestContext
from django.template.loader_tags import BlockNode, ExtendsNode
from django.utils.html import strip_tags
from django.template import TemplateDoesNotExist, Template as BaseTemplate

from premailer import Premailer

from .. import settings
from ..compat import BaseEngine, _dirs_undefined, import_string

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

    def __init__(self, params):
        self.name = params.get('NAME')
        dirs = list(params.get('DIRS', []))
        app_dirs = bool(params.get('APP_DIRS', False))
        options = params.get('OPTIONS', {}).copy()
        libraries = options.get('libraries', {})
        options['libraries'] = self.get_templatetag_libraries(libraries)
        super(EmlEngine, self).__init__(dirs=dirs, app_dirs=app_dirs, **options)

    def get_templatetag_libraries(self, custom_libraries):
        """
        Return a collation of template tag libraries from installed
        applications and the supplied custom_libraries argument.
        """
        from django.template.backends.django import get_installed_libraries
        libraries = get_installed_libraries()
        libraries.update(custom_libraries)
        return libraries

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
        if template_name and template_name.endswith('.eml'):
            return super(EmlEngine, self).get_template(template_name, dirs=dirs)
        raise TemplateDoesNotExist(template_name)


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

    def _send(self, recipients, context, from_email=None, bcc=None, cc=None,
              reply_to=None, attachments=None):
        #pylint: disable=too-many-locals
        if reply_to:
            headers = {'Reply-To': reply_to}
        else:
            headers = None

        nodes = self
        extend = None
        subject = None
        html_content = None
        plain_content = None

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
                            # 'django.core.context_processors.request' must be
                            # present in TEMPLATE_CONTEXT_PROCESSORS.
                            lnk['href'] = build_absolute_uri(
                                context.get('request', None), href)
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


    #pylint: disable=invalid-name,too-many-arguments
    def send(self, recipients, context,
             from_email=None, bcc=None, cc=None, reply_to=None,
             attachments=None):
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL
        if not isinstance(context, Context):
            context = RequestContext(None, context)

        if hasattr(context, 'template') and context.template is None:
            with context.bind_template(self):
                context.template_name = self.name
                return self._send(recipients, context, from_email=from_email,
                    bcc=bcc, cc=cc, reply_to=reply_to, attachments=attachments)
        else:
            return self._send(recipients, context, from_email=from_email,
                bcc=bcc, cc=cc, reply_to=reply_to, attachments=attachments)
