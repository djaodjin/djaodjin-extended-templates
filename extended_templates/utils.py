# Copyright (c) 2024, DjaoDjin inc.
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

import logging, os

from django.conf import settings as django_settings
from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import RegexValidator
from django.core.files.storage import FileSystemStorage
from django.utils.module_loading import import_string

from . import settings
from .compat import (gettext_lazy as _, import_string, urljoin,
    get_storage_class)

LOGGER = logging.getLogger(__name__)


validate_title = RegexValidator(#pylint: disable=invalid-name
    r'^[a-zA-Z0-9- ]+$',
    _("Enter a valid title consisting of letters, "
        "numbers, space, underscores or hyphens."),
        'invalid'
)


def get_assets_dirs():
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


def get_account_model():
    """
    Returns the ``Account`` model that is active in this project.
    """
    try:
        return django_apps.get_model(settings.ACCOUNT_MODEL)
    except ValueError:
        raise ImproperlyConfigured(
            "ACCOUNT_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured("ACCOUNT_MODEL refers to model '%s'"\
" that has not been installed" % settings.ACCOUNT_MODEL)


def get_current_account():
    """
    Returns the default account for a site.
    """
    account = None
    if settings.DEFAULT_ACCOUNT_CALLABLE:
        account = import_string(settings.DEFAULT_ACCOUNT_CALLABLE)()
        LOGGER.debug("get_current_account: '%s'", account)
    return account


def get_default_storage(request, account=None, **kwargs):
    """
    Returns the default storage for an account.
    """
    account = None
    if settings.DEFAULT_STORAGE_CALLABLE:
        storage = import_string(settings.DEFAULT_STORAGE_CALLABLE)(
            request, account=account, **kwargs)
        LOGGER.debug("get_default_storage('%s')=%s", account, storage)
        return storage
    return get_default_storage_base(request, account=account, **kwargs)


def get_default_storage_base(request, account=None, public=False, **kwargs):
    # default implementation
    storage_class = get_storage_class()
    if storage_class.__name__.endswith('3Storage'):
        # Hacky way to test for `storages.backends.s3.S3Storage`
        # and `storages.backends.s3boto3.S3Boto3Storage` without importing
        # the optional package 'django-storages'.
        storage_kwargs = {}
        storage_kwargs.update(**kwargs)
        if public:
            storage_kwargs.update({'default_acl': 'public-read'})
        for key in ['access_key', 'secret_key']:
            if key in request.session:
                storage_kwargs[key] = request.session[key]
        bucket_name = _get_bucket_name(account)
        location = _get_media_prefix(account)
        LOGGER.debug("create %s(bucket_name='%s', location='%s', %s)",
            storage_class.__name__, bucket_name, location, storage_kwargs)
        storage = storage_class(bucket_name=bucket_name, location=location,
            **storage_kwargs)
        if 'security_token' in request.session:
            storage.security_token = request.session['security_token']
        return storage
    LOGGER.debug("``%s`` does not contain ``3Storage`` in its name,"\
        " default to FileSystemStorage.", storage_class)
    return _get_file_system_storage(account)


def _get_bucket_name(account=None):
    if account:
        for bucket_field in settings.BUCKET_NAME_FROM_FIELDS:
            try:
                bucket_name = getattr(account, bucket_field)
                if bucket_name:
                    return bucket_name
            except AttributeError:
                pass
    return settings.AWS_STORAGE_BUCKET_NAME


def _get_file_system_storage(account=None):
    location = settings.MEDIA_ROOT
    base_url = settings.MEDIA_URL
    prefix = _get_media_prefix(account)
    parts = location.split(os.sep)
    if prefix and prefix != parts[-1]:
        location = os.sep.join(parts[:-1] + [prefix, parts[-1]])
        if base_url.startswith('/'):
            base_url = base_url[1:]
        base_url = urljoin("/%s/" % prefix, base_url)
    return FileSystemStorage(location=location, base_url=base_url)


def _get_media_prefix(account=None):
    media_prefix = settings.MEDIA_PREFIX
    if account:
        try:
            media_prefix = account.media_prefix
        except AttributeError:
            LOGGER.debug("``%s`` does not contain a ``media_prefix``"\
                " field.", account.__class__)
        if not media_prefix:
            media_prefix = str(account)
    return media_prefix
