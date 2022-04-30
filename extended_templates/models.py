# Copyright (c) 2022, Djaodjin Inc.
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

from __future__ import unicode_literals

import logging

from django.db import models

from . import settings
from .compat import import_string, python_2_unicode_compatible


LOGGER = logging.getLogger(__name__)


def get_extra_field_class():
    extra_class = settings.EXTRA_FIELD
    if extra_class is None:
        extra_class = models.TextField
    elif isinstance(extra_class, str):
        extra_class = import_string(extra_class)
    return extra_class


@python_2_unicode_compatible
class MediaTag(models.Model):

    location = models.CharField(max_length=250)
    tag = models.CharField(max_length=50)

    def __str__(self):
        return str(self.tag)


@python_2_unicode_compatible
class LessVariable(models.Model):
    """
    This model stores value of a variable used to generate a css file.
    """
    name = models.CharField(max_length=250)
    value = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    account = models.ForeignKey(settings.ACCOUNT_MODEL,
        null=True, on_delete=models.SET_NULL,
        related_name='account_less_variable')
    cssfile = models.CharField(max_length=50)

    class Meta:
        unique_together = ('account', 'cssfile', 'name')

    def __str__(self):
        return '%s: %s' % (self.name, self.value)


@python_2_unicode_compatible
class ThemePackage(models.Model):
    """
    This model allow to record uploaded template.
    """
    slug = models.SlugField(unique=True)
    account = models.ForeignKey(
        settings.ACCOUNT_MODEL, null=True, on_delete=models.CASCADE,
        related_name='account_template', blank=True)
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        if self.account:
            return '%s-%s' % (self.account, self.name)
        return self.name


def get_active_theme():
    """
    Returns the active theme from a request.
    """
    if settings.ACTIVE_THEME_CALLABLE:
        return import_string(settings.ACTIVE_THEME_CALLABLE)()
    return settings.APP_NAME
