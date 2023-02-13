# Copyright (c) 2023, Djaodjin Inc.
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
import logging, subprocess

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand

from ...api.sources import process_template


LOGGER = logging.getLogger(__name__)


class AggregateCSSClassesVisitor(object):

    def __init__(self, template_path=None):
        self.template_path = template_path
        self.css_classes = set([])

    def update_block(self, block_text):
        #pylint:disable=too-many-arguments
        LOGGER.debug("%slooking in '%s'",
            "(%s) " % self.template_path if self.template_path else "",
            block_text)
        soup = BeautifulSoup(block_text, 'html5lib')
        for tag in soup.find_all(True):
            try:
                self.css_classes |= set(tag["class"])
            except KeyError:
                continue

    def push_text(self, text):
        pass


class Command(BaseCommand):
    """
    Lists CSS classes used in a set of templates
    """

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('template_paths', nargs='*',
            help='list of templates')

    def handle(self, *args, **options):
        visitor = AggregateCSSClassesVisitor()
        for template_path in options['template_paths']:
            process_template(visitor, template_path=template_path)
        self.stdout.write("CSS classes found:")
        for css_class in sorted(visitor.css_classes):
            cmd = ["grep", "-rl", "'\.%s'" % str(css_class),
                settings.BASE_DIR]
            try:
                lines = subprocess.check_output(" ".join(cmd), shell=True)
                if hasattr(lines, 'decode'):
                    lines = lines.decode('utf-8').split('\n')
                self.stdout.write(".%s:" % str(css_class))
                for line in lines:
                    self.stdout.write("\t%s" % line)
            except subprocess.CalledProcessError:
                #self.stdout.write(".%s: not found" % str(css_class))
                pass

