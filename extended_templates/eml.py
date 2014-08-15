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

from bs4 import BeautifulSoup
from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.template import Context
from django.template.loader_tags import BlockNode
from django.utils.html import strip_tags
from django.template import Template

from extended_templates import settings


class EmlTemplateError(Exception):
    pass


class EmlTemplate(Template):
    """
    Sends an email to a list of recipients (i.e. email addresses).
    """

    def __init__(self, template_string, origin=None, name='<Unknown Template>'):
        super(EmlTemplate, self).__init__(template_string, origin, name)
        self.origin = origin

    #pylint: disable=invalid-name,too-many-arguments
    def send(self, recipients, context,
             from_email=None, bcc=None, cc=None):
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL
        subject = None
        html_content = None
        plain_content = None
        context = Context(context)
        for node in self:
            if isinstance(node, BlockNode):
                if node.name == 'subject':
                    # Email subject *must not* contain newlines
                    subject = ''.join(node.render(context).splitlines())
                elif  node.name == 'html_content':
                    html_content = node.render(context)
                    soup = BeautifulSoup(html_content)
                    for lnk in soup.find_all('a'):
                        href = lnk.get('href')
                        if href and href.startswith('/'):
                            lnk['href'] = 'http://%s%s' % (
                                Site.objects.get_current(), href)
                    html_content = soup.prettify()
                elif  node.name == 'plain_content':
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
        msg = EmailMultiAlternatives(
            subject, plain_content, from_email, recipients, bcc=bcc, cc=cc)
        if html_content:
            msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=True)
