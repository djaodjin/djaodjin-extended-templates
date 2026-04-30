# Copyright (c) 2026, Djaodjin Inc.
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


import hashlib, logging, os

import boto3
from django.db import transaction
from rest_framework import parsers, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response as HttpResponse

from .serializers import AssetSerializer, MediaItemListSerializer
from .. import settings
from ..compat import force_str, gettext_lazy as _, urlparse, urlunparse
from ..docs import extend_schema, OpenApiResponse
from ..mixins import AccountMixin
from ..models import MediaTag
from ..utils import _get_media_prefix, validate_title, get_default_storage


LOGGER = logging.getLogger(__name__)

URL_PATH_SEP = '/'


class ListUploadAssetAPIView(AccountMixin, ListCreateAPIView):
    """
    Lists uploaded static asset files

    **Examples

    .. code-block:: http

        GET /api/themes/assets/ HTTP/1.1

    responds

    .. code-block:: json

        {
          "count": 1,
          "previous": null,
          "next": null,
          "results": [{
              "location": "https://example-bucket.s3.amazon.com\
/supporting-evidence.pdf",
              "updated_at": "2016-10-26T00:00:00.00000+00:00",
              "tags": []
          }]
        }
    """
    store_hash = True
    replace_stored = False
    content_type = None
    serializer_class = AssetSerializer
    pagination_class = PageNumberPagination
    parser_classes = (parsers.JSONParser, parsers.FormParser,
        parsers.MultiPartParser, parsers.FileUploadParser)

    def resolve_asset_location(self, location):
        return location


    def list_media(self, storage, includes=None, prefix='.'):
        """
        Returns a list of media from storage
        """
        assets = []
        try:
            dirs, files = storage.listdir(prefix)
            for asset in files:
                if prefix and prefix != '.':
                    asset = URL_PATH_SEP.join([prefix, asset])
                location = storage.url(asset)
                # The URL might contain temporary auth/permission tokens
                parts = urlparse(location)
                permanent_location = urlunparse(
                    (parts.scheme, parts.netloc, parts.path, None, None, None))
                location = self.resolve_asset_location(location)
                if includes is None or location in includes:
                    media_tags = MediaTag.objects.filter(
                        location=permanent_location)
                    assets += [{
                        'location': location,
                        'updated_at': storage.get_modified_time(asset),
                        'tags': media_tags.values_list('tag', flat=True)
                    }]
            for asset_dir in dirs:
                if prefix and prefix != '.':
                    asset_dir = URL_PATH_SEP.join([prefix, asset_dir])
                assets += self.list_media(storage, includes, prefix=asset_dir)
        except OSError:
            if storage.exists('.'):
                LOGGER.exception(
                    "Unable to list objects in %s.", storage.__class__.__name__)
            raise ValidationError({
                'detail': _("cannot access assets storage.")})

        except storage.connection_response_error:
            LOGGER.exception(
                "Unable to list objects in 's3://%s/%s/%s'.",
                storage.bucket_name, storage.location, prefix)
            raise ValidationError({
                'detail': _("cannot access assets storage.")})

        return assets


    def get_serializer_class(self):
        if self.request.method.lower() in ('put', 'patch'):
            return MediaItemListSerializer
        return super(ListUploadAssetAPIView, self).get_serializer_class()

    def get(self, request, *args, **kwargs):
        #pylint:disable=unused-argument,unused-variable
        locations = None
        search = request.GET.get('q')
        if search:
            validate_title(search)
            locations = MediaTag.objects.filter(tag__icontains=search)\
                .values_list('location', flat=True)
        assets = self.list_media(
            get_default_storage(request, self.account), includes=locations)
        results = AssetSerializer(many=True).to_representation(assets)
        return self.get_paginated_response(results)

    def get_paginated_response(self, data):
        # XXX - Deactivate pagination until not
        # implemented in djaodjin-sidebar-gallery
        # page = self.paginate_queryset(queryset['results'])
        # if page is not None:
        #     queryset = {'count': len(page), 'results' : page}
        total_count = len(data)
        # sort assets by updated_at to sort by created_at.
        # Media are not updated, so updated_at = created_at
        return HttpResponse({
            'count': total_count,
            'results': sorted(data, key=lambda x: x['updated_at'])
        })

    def post(self, request, *args, **kwargs):
        """
        Uploads a static asset file

        **Examples

        .. code-block:: http

            POST /api/themes/assets/ HTTP/1.1

        responds

        .. code-block:: json

            {
              "location": "/media/image-001.jpg",
              "updated_at": "2016-10-26T00:00:00.00000+00:00",
              "tags": []
            }
        """
        is_public_asset = request.query_params.get('public', False)
        response_data, response_status = process_upload(
            request, account=self.account, is_public_asset=is_public_asset,
            store_hash=self.store_hash, replace_stored=self.replace_stored,
            content_type=self.content_type,
            media_prefix=_get_media_prefix(self.account))
        response_data['location'] = self.resolve_asset_location(
            response_data['location'])
        return HttpResponse(
            AssetSerializer().to_representation(response_data),
            status=response_status)

    def delete(self, request, *args, **kwargs):
        """
        Deletes static assets file

        **Examples

        .. code-block:: http

            DELETE /api/themes/assets/?location=/media/item/url1.jpg HTTP/1.1

        """
        #pylint: disable=unused-variable,unused-argument,too-many-locals
        storage = get_default_storage(request, self.account)
        assets = self.list_media(storage,
            includes=[request.query_params.get('location')])
        if not assets:
            return HttpResponse({}, status=status.HTTP_404_NOT_FOUND)

        base = storage.url('')
        for item in assets:
            parts = urlparse(item['location'])
            permanent_location = urlunparse(
                (parts.scheme, parts.netloc, parts.path, None, None, None))
            if permanent_location.startswith(base):
                storage.delete(permanent_location[len(base):])
            MediaTag.objects.filter(location=permanent_location).delete()
        return HttpResponse({'detail': _('Media correctly deleted.')},
            status=status.HTTP_200_OK)

    @extend_schema(responses={
      200: OpenApiResponse(AssetSerializer(many=True))})
    def put(self, request, *args, **kwargs):
        """
        Updates meta tags on assets

        **Examples

        .. code-block:: http

            PUT /api/themes/assets/ HTTP/1.1

        .. code-block:: json

            {
                "items": [
                    {"location": "/media/item/url1.jpg"},
                    {"location": "/media/item/url2.jpg"}
                ],
                "tags": ["photo", "homepage"]
            }

        When the API returns, both assets file listed in items will be tagged
        with 'photo' and 'homepage'. Those tags can then be used later on
        in searches.

        responds

        .. code-block:: json

            {
              "count": 1,
              "previous": null,
              "next": null,
              "results": [{
                  "location": "/media/image-001.jpg",
                  "updated_at": "2016-10-26T00:00:00.00000+00:00",
                  "tags": ""
              }]
            }
        """
        #pylint:disable=too-many-locals
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        storage = get_default_storage(request, self.account)
        assets = self.list_media(storage, includes=[item.get('location')
                for item in serializer.validated_data['items']])
        if not assets:
            return HttpResponse({}, status=status.HTTP_404_NOT_FOUND)

        base_url_pat = self.resolve_asset_location('')
        tags = [tag for tag in serializer.validated_data.get('tags') if tag]
        for item in assets:
            permanent_location = item['location']
            if base_url_pat and permanent_location.startswith(base_url_pat):
                key_name = permanent_location[len(base_url_pat):].lstrip(
                    URL_PATH_SEP)
                # we remove leading '/' otherwise S3 copy triggers a 404
                # because it creates an URL with '//'.
                permanent_location = storage.url(key_name)
                parts = urlparse(permanent_location)
                permanent_location = urlunparse(
                    (parts.scheme, parts.netloc, parts.path, None, None, None))
            with transaction.atomic():
                media_tags = MediaTag.objects.filter(
                    location=permanent_location)
                for tag in tags:
                    MediaTag.objects.get_or_create(
                        location=permanent_location, tag=tag)
                # Remove tags which are no more set for the permanent_location.
                media_tags.exclude(tag__in=tags).delete()

            # Update tags returned by the API.
            media_tags = MediaTag.objects.filter(location=permanent_location)
            item['tags'] = media_tags.values_list('tag', flat=True)

        serializer = self.serializer_class(
            sorted(assets, key=lambda x: x['updated_at']), many=True)
        http_resp = self.get_paginated_response(serializer.data)
        http_resp.data.update({'detail': _("Tags correctly updated.")})
        return http_resp


def process_upload(request, storage=None, account=None, is_public_asset=None,
                   store_hash=True, replace_stored=False, content_type=None,
                   media_prefix=None):
    #pylint:disable=too-many-arguments,too-many-locals
    response_status = status.HTTP_200_OK
    if not storage:
        storage = get_default_storage(request, account)

    location = request.data.get('location', None)
    if location:
        parts = urlparse(location)
        bucket_name = parts.netloc.split('.')[0]
        src_key_name = parts.path.lstrip(URL_PATH_SEP)
        # we remove leading '/' otherwise S3 copy triggers a 404
        # because it creates an URL with '//'.
        prefix = os.path.dirname(src_key_name)
        if prefix:
            prefix += URL_PATH_SEP
        ext = os.path.splitext(src_key_name)[1]

        s3_client = boto3.client('s3')
        data = s3_client.get_object(Bucket=bucket_name, Key=src_key_name)
        uploaded_file = data['Body']
        dst_key_name = "%s%s%s" % (prefix,
            hashlib.sha256(uploaded_file.read()).hexdigest(), ext)
        LOGGER.info("copy s3://%s/%s to s3://%s/%s",
                    bucket_name, src_key_name, bucket_name, dst_key_name)
        if is_public_asset:
            extra_args = {'ACL': "public-read"}
        else:
            extra_args = {
                'ServerSideEncryption': settings.AWS_SERVER_SIDE_ENCRYPTION}
        if ext in ['.pdf']:
            extra_args.update({'ContentType': 'application/pdf'})
        elif ext in ['.jpg']:
            extra_args.update({'ContentType': 'image/jpeg'})
        elif ext in ['.png']:
            extra_args.update({'ContentType': 'image/png'})
        s3_client.copy({'Bucket': bucket_name, 'Key': src_key_name},
            bucket_name, dst_key_name, ExtraArgs=extra_args)
        # XXX still can't figure out why we get a permission denied
        # on DeleteObject.
        if False:
            s3_client.delete_object(Bucket=bucket_name, Key=src_key_name)

        storage_key_name = dst_key_name
        if media_prefix and storage_key_name.startswith(media_prefix):
            storage_key_name = storage_key_name[len(media_prefix) + 1:]

    elif 'file' in request.data:
        uploaded_file = request.data['file']
        if content_type:
            # We optionally force the content_type because S3Store uses
            # mimetypes.guess and surprisingly it doesn't get it correct
            # for 'text/css'.
            uploaded_file.content_type = content_type
        sha = hashlib.sha256(uploaded_file.read()).hexdigest()

        # Store filenames with forward slashes, even on Windows
        filename = force_str(uploaded_file.name.replace('\\', '/'))
        sha_filename = sha + os.path.splitext(filename)[1]
        storage_key_name = sha_filename if store_hash else filename
        if not is_public_asset:
            assert account is not None
            storage_key_name = '/'.join([str(account), storage_key_name])

        LOGGER.info("upload %s to %s", filename, storage_key_name)
        if storage.exists(storage_key_name) and replace_stored:
                storage.delete(storage_key_name)
        if not storage.exists(storage_key_name):
            storage.save(storage_key_name, uploaded_file)
            response_status = status.HTTP_201_CREATED

    else:
        raise ValidationError({'detail':
           _("Either 'location' or 'file' must be specified.")})

    return ({
        'location': storage.url(storage_key_name),
        'updated_at': storage.get_modified_time(storage_key_name)
    }, response_status)
