# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE

from __future__ import absolute_import

import logging

from django.conf import settings
import django.template.defaulttags
from django.utils.translation import gettext, ngettext
from django.utils._os import safe_join
from deployutils.apps.django.themes import get_template_search_path
from extended_templates import signals as extended_templates_signals
from jinja2.ext import i18n
from jinja2.sandbox import SandboxedEnvironment as Jinja2Environment
from extended_templates.compat import import_string, reverse, six

import testsite.templatetags.testsite_tags


LOGGER = logging.getLogger(__name__)


class TestsiteEnvironment(Jinja2Environment):

    def get_template(self, name, parent=None, globals=None):
        #pylint:disable=redefined-builtin
        template = super(TestsiteEnvironment, self).get_template(
            name, parent=parent, globals=globals)
        LOGGER.info("[TestsiteEnvironment.get_template] loads %s from %s" % (
            name, template.filename))
        extended_templates_signals.template_loaded.send(
            sender=self, template=template)
        return template


def environment(**options):
    # If we don't force ``auto_reload`` to True, in DEBUG=0, the templates
    # would only be compiled on the first edit.
    options.update({'auto_reload': True, 'cache_size': 0})
    if 'loader' in options:
        if isinstance(options['loader'], six.string_types):
            loader_class = import_string(options['loader'])
        else:
            loader_class = options['loader'].__class__
        template_search_paths = get_template_search_path()
        template_search_paths += [safe_join(settings.BASE_DIR, 'extended_templates', 'templates')]
        print("XXX %s(%s)" % (loader_class, template_search_paths))
        options['loader'] = loader_class(template_search_paths)
    env = TestsiteEnvironment(extensions=[i18n], **options)
    # i18n
    env.install_gettext_callables(gettext=gettext, ngettext=ngettext,
        newstyle=True)
    # filters
    env.filters['messages'] = testsite.templatetags.testsite_tags.messages
    env.filters['to_json'] = testsite.templatetags.testsite_tags.to_json

    env.globals.update({
        'DATETIME_FORMAT': "MMM dd, yyyy",
    })
    if settings.DEBUG:
        env.filters['addslashes'] = django.template.defaultfilters.addslashes
        env.globals.update({
            'url': reverse,
            'cycle': django.template.defaulttags.cycle,
        })

    return env
