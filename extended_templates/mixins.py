# Copyright (c) 2022 DjaoDjin inc.
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

import logging

import markdown
from bs4 import BeautifulSoup
from django.utils._os import safe_join

from . import settings
from .compat import import_string, six, urlsplit
from .models import MediaTag, get_active_theme
from .extras import AccountMixinBase


LOGGER = logging.getLogger(__name__)


class AccountMixin(AccountMixinBase, settings.EXTRA_MIXIN):
    pass


class UploadedImageMixin(object):

    def build_filter_list(self, validated_data):
        items = validated_data.get('items')
        filter_list = []
        if items:
            for item in items:
                location = item['location']
                parts = urlsplit(location)
                if parts.netloc == self.request.get_host():
                    location = parts.path
                filter_list += [location]
        return filter_list

    def list_media(self, storage, filter_list, prefix='.'):
        """
        Return a list of media from default storage
        """
        #pylint:disable=too-many-locals
        results = []
        total_count = 0
        if prefix.startswith('/'):
            prefix = prefix[1:]
        try:
            dirs, files = storage.listdir(prefix)
            for media in files:
                if prefix and prefix != '.':
                    media = prefix + '/' + media
                if not media.endswith('/') and media != "":
                    total_count += 1
                    location = storage.url(media)
                    try:
                        updated_at = storage.get_modified_time(media)
                    except AttributeError: # Django<2.0
                        updated_at = storage.modified_time(media)
                    normalized_location = location.split('?')[0]
                    if (filter_list is None
                        or normalized_location in filter_list):
                        tags = ",".join(list(MediaTag.objects.filter(
                            location=normalized_location).values_list(
                            'tag', flat=True)))
                        results += [
                            {'location': location,
                            'tags': tags,
                            'updated_at': updated_at
                            }]
            for asset_dir in dirs:
                dir_results, dir_total_count = self.list_media(
                    storage, filter_list, prefix=prefix + '/' + asset_dir)
                results += dir_results
                total_count += dir_total_count
        except OSError:
            if storage.exists('.'):
                LOGGER.exception(
                    "Unable to list objects in %s.", storage.__class__.__name__)
        except storage.connection_response_error:
            LOGGER.exception(
                "Unable to list objects in 's3://%s/%s/%s'.",
                storage.bucket_name, storage.location, prefix)

        # sort results by updated_at to sort by created_at.
        # Media are not updated, so updated_at = created_at
        return results, total_count


class ThemePackageMixin(AccountMixin):

    theme_url_kwarg = 'theme'

    @property
    def theme(self):
        if not hasattr(self, '_theme'):
            self._theme = self.kwargs.get(self.theme_url_kwarg)
            if not self._theme:
                self._theme = get_active_theme()
        return self._theme

    @staticmethod
    def get_templates_dir(theme):
        if isinstance(settings.THEME_DIR_CALLABLE, six.string_types):
            settings.THEME_DIR_CALLABLE = import_string(
                settings.THEME_DIR_CALLABLE)
        theme_dir = settings.THEME_DIR_CALLABLE(theme)
        return safe_join(theme_dir, 'templates')


class UpdateEditableMixin(object):
    """
    Edit an element in a page.
    """
    @staticmethod
    def insert_formatted(editable, new_text):
        new_text = BeautifulSoup(new_text, 'html5lib')
        for image in new_text.find_all('img'):
            image['style'] = "max-width:100%"
        if editable.name == 'div':
            editable.clear()
            editable.append(new_text)
        else:
            editable.string = "ERROR : Impossible to insert HTML into \
                \"<%s></%s>\" element. It should be \"<div></div>\"." %\
                (editable.name, editable.name)
            editable['style'] = "color:red;"
            # Prevent edition of error notification
            editable['class'] = editable['class'].remove("editable")

    @staticmethod
    def insert_currency(editable, new_text):
        amount = float(new_text)
        editable.string = "$%.2f" % (amount/100)

    @staticmethod
    def insert_markdown(editable, new_text):
        new_text = markdown.markdown(new_text,)
        new_text = BeautifulSoup(new_text, 'html.parser')
        for image in new_text.find_all('img'):
            image['style'] = "max-width:100%"
        editable.name = 'div'
        editable.string = ''
        children_done = []
        for element in new_text.find_all():
            if element.name not in ('html', 'body'):
                if element.findChildren():
                    for sub_el in element.findChildren():
                        element.append(sub_el)
                        children_done += [sub_el]
                if not element in children_done:
                    editable.append(element)
