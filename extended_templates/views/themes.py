# Copyright (c) 2023, DjaoDjin inc.
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

import logging, os, shutil, tempfile, zipfile
from io import BytesIO

from django.http import HttpResponse
from django.views.generic import TemplateView, View
from deployutils.apps.django.themes import package_theme

from .. import settings
from ..mixins import AccountMixin, ThemePackageMixin


LOGGER = logging.getLogger(__name__)


class ThemePackagesView(AccountMixin, TemplateView):

    template_name = "extended_templates/theme.html"


class ThemePackageDownloadView(ThemePackageMixin, View):

    @staticmethod
    def write_zipfile(zipf, dir_path, dir_option=""):
        for dirname, _, files in os.walk(dir_path):
            for filename in files:
                abs_file_path = os.path.join(
                    dirname, filename)
                rel_file_path = os.path.join(
                    dir_option,
                    abs_file_path.replace("%s/" % dir_path, ''))
                LOGGER.debug("zip %s as %s", abs_file_path, rel_file_path)
                zipf.write(abs_file_path, rel_file_path)
        return zipf

    def install_assets(self, srcroot, destroot):
        """
        Copy the assets in srcroot to destroot.
        """
        if not os.path.isdir(srcroot):
            return
        if not os.path.exists(destroot):
            os.makedirs(destroot)
        for pathname in os.listdir(srcroot):
            source_name = os.path.join(srcroot, pathname)
            dest_name = os.path.join(destroot, pathname)
            LOGGER.debug("%s %s %s", "install" if (
                os.path.isfile(source_name) and
                not os.path.exists(dest_name)) else "pass",
                source_name, dest_name)
            if os.path.isfile(source_name) and not os.path.exists(dest_name):
                # We don't want to overwrite specific theme files by generic
                # ones.
                shutil.copyfile(source_name, dest_name)
            elif os.path.isdir(source_name):
                self.install_assets(source_name, dest_name)

    def package_assets(self, app_name, build_dir):
        # assets_dir = get_assets_dirs()
        # We are not using `get_assets_dirs()` before we can filter only
        # the static files used in templates. We don't want all of HTDOCS.
        assets_dir = [os.path.join(settings.PUBLIC_ROOT, self.theme)]
        for base_path in assets_dir:
            self.install_assets(base_path, os.path.join(build_dir, 'public'))

    def get(self, *args, **kwargs): #pylint:disable=unused-argument
        content = BytesIO()
        build_dir = tempfile.mkdtemp(prefix="pages-")
        try:
            package_theme(self.theme, build_dir,
                excludes=settings.TEMPLATES_BLACKLIST)
            self.package_assets(self.theme, build_dir)
            # We don't use deployutils fill_package because we need
            # a buffer.
            with zipfile.ZipFile(content, mode="w") as zipf:
                zipf = self.write_zipfile(zipf, build_dir, self.theme)
        finally:
            shutil.rmtree(build_dir)
        content.seek(0)

        resp = HttpResponse(content.read(), content_type='application/x-zip')
        resp['Content-Disposition'] = 'attachment; filename="{}"'.format(
                "%s.zip" % self.theme)
        return resp
