# Copyright (c) 2022, DjaoDjin inc.
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

from django.conf import settings as django_settings

from .compat import import_string, six


def build_absolute_uri(request, location='', site=None):
    from . import settings
    if location.startswith('http://') or location.startswith('https://'):
        # already an absolute url.
        return location
    if settings.BUILD_ABSOLUTE_URI_CALLABLE:
        return import_string(settings.BUILD_ABSOLUTE_URI_CALLABLE)(
            request, location=location, site=site)
    return request.build_absolute_uri(location=location)


def get_assets_dirs():
    from . import settings
    if settings.ASSETS_DIRS_CALLABLE:
        return import_string(settings.ASSETS_DIRS_CALLABLE)()
    candidates = getattr(django_settings, 'STATICFILES_DIRS', None)
    if not candidates:
        static_root = getattr(django_settings, 'STATIC_ROOT', None)
        if static_root:
            candidates = [static_root]
    assets_dirs = []
    static_prefix = django_settings.STATIC_URL.rstrip('/')
    for asset_dir in candidates:
        if asset_dir.endswith(static_prefix):
            asset_dir = asset_dir[:-len(static_prefix)]
        assets_dirs += [asset_dir]
    return assets_dirs


def update_context_urls(context, urls):
    if 'urls' in context:
        for key, val in six.iteritems(urls):
            if key in context['urls']:
                if isinstance(val, dict):
                    context['urls'][key].update(val)
                else:
                    # Because organization_create url is added in this mixin
                    # and in ``OrganizationRedirectView``.
                    context['urls'][key] = val
            else:
                context['urls'].update({key: val})
    else:
        context.update({'urls': urls})
    return context
