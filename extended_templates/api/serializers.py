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
from __future__ import unicode_literals

from rest_framework import serializers

from ..compat import gettext_lazy as _
from ..models import LessVariable, ThemePackage

#pylint: disable=abstract-method


class NoModelSerializer(serializers.Serializer):

    def create(self, validated_data):
        raise RuntimeError('`create()` should not be called.')

    def update(self, instance, validated_data):
        raise RuntimeError('`update()` should not be called.')


class LessVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessVariable
        fields = ('name', 'value', 'created_at', 'updated_at')
        # Implementation Note: Without this ``extra_kwargs``, DRF will complain
        # with a "<Model> with this <field> already exists" error
        # when attempting to update a list of objects.
        extra_kwargs = {
            'name': {'validators': []},
        }

class ThemePackageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ThemePackage
        fields = ('slug', 'name', 'created_at', 'updated_at', 'is_active')


class AssetSerializer(NoModelSerializer):

    location = serializers.CharField(
        help_text=_("URL where the asset content is stored."))
    updated_at = serializers.DateTimeField(required=False,
        help_text=_("Last date/time the asset content was updated."))
    tags = serializers.CharField(required=False, allow_blank=True,
        help_text=_("Tags associated to the asset."))

class MediaItemListSerializer(NoModelSerializer):

    items = AssetSerializer(many=True)
    tags = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False)


class EditionFileSerializer(serializers.Serializer):
    text = serializers.CharField(allow_blank=True)


class SourceCodeSerializer(NoModelSerializer):

    path = serializers.CharField(required=False, max_length=255)
    text = serializers.CharField(required=False, max_length=100000)


class HintSerializer(NoModelSerializer):

    index = serializers.IntegerField()
    name = serializers.CharField()


class SourceElementSerializer(SourceCodeSerializer):

    hints = serializers.ListField(
        child=HintSerializer(), required=False)
