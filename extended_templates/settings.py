# Copyright (c) 2018, Djaodjin Inc.
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

"""
Convenience module for access of extended_templates app settings, which enforces
default settings when the main settings module does not contain
the appropriate settings.
"""

import os, sys

from django.conf import settings
from django.utils._os import safe_join


_SETTINGS = {
    'ASSETS_MAP': {},
    'ASSETS_CACHE_DIR': (
        settings.STATIC_ROOT if settings.STATIC_ROOT
        else settings.STATICFILES_DIRS[0]),
    'ASSETS_SOURCES_DIR': safe_join(
        settings.BASE_DIR, os.path.basename(settings.BASE_DIR),
        'static', 'scss'),
    'ASSETS_DIRS_CALLABLE': None,
    'BUILD_ABSOLUTE_URI_CALLABLE': None,
    'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL'),
    'EMAILER_BACKEND': getattr(settings, 'EMAILER_BACKEND',
        'extended_templates.backends.TemplateEmailBackend'),
    'PDF_FLATFORM_BIN': safe_join(
        os.path.dirname(sys.executable), 'podofo-flatform'),
    'SASSC_BIN': safe_join(
        os.path.dirname(sys.executable), 'sassc'),
    'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/')
}
_SETTINGS.update(getattr(settings, 'EXTENDED_TEMPLATES', {}))

ASSETS_MAP = _SETTINGS.get('ASSETS_MAP')
ASSETS_CACHE_DIR = _SETTINGS.get('ASSETS_CACHE_DIR')
ASSETS_SOURCES_DIR = _SETTINGS.get('ASSETS_SOURCES_DIR')
ASSETS_DIRS_CALLABLE = _SETTINGS.get('ASSETS_DIRS_CALLABLE')
BUILD_ABSOLUTE_URI_CALLABLE = _SETTINGS.get('BUILD_ABSOLUTE_URI_CALLABLE')
DEFAULT_FROM_EMAIL = _SETTINGS.get('DEFAULT_FROM_EMAIL')
EMAILER_BACKEND = _SETTINGS.get('EMAILER_BACKEND')
PDF_FLATFORM_BIN = _SETTINGS.get('PDF_FLATFORM_BIN')
SASSC_BIN = _SETTINGS.get('SASSC_BIN')
STATIC_URL = _SETTINGS.get('STATIC_URL')
