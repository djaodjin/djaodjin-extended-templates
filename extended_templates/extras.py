# Copyright (c) 2025, DjaoDjin inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from django.shortcuts import get_object_or_404

from .compat import NoReverseMatch, reverse
from .helpers import update_context_urls
from .utils import get_account_model, get_current_account


class AccountMixinBase(object):

    account_url_kwarg = None

    @property
    def account(self):
        if not hasattr(self, '_account'):
            self._account = self.get_account()
        return self._account

    def get_account(self):
        if not self.account_url_kwarg:
            #pylint:disable=import-outside-toplevel
            from . import settings
            self.account_url_kwarg = settings.ACCOUNT_URL_KWARG
        if self.account_url_kwarg in self.kwargs:
            return get_object_or_404(get_account_model(),
                slug=self.kwargs.get(self.account_url_kwarg))
        return get_current_account()

    def get_context_data(self, **kwargs):
        context = super(AccountMixinBase, self).get_context_data(**kwargs)
        url_kwargs = {}
        try:
            context = update_context_urls(context, {
                'api_sources': reverse(
                    'extended_templates_api_sources', kwargs=url_kwargs),})
        except NoReverseMatch:
            # Page editor is optional
            pass
        try:
            context = update_context_urls(context, {
                'api_themes': reverse(
                    'extended_templates_api_themes', kwargs=url_kwargs),
                'theme_update': reverse(
                    'extended_templates_theme_update', kwargs=url_kwargs),
                'theme_download': reverse(
                    'extended_templates_theme_download', kwargs=url_kwargs)})
        except NoReverseMatch:
            # Themes are optional
            pass
        return context
