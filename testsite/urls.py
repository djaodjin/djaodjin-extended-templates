# Copyright (c) 2025, Djaodjin Inc.
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

from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from extended_templates.compat import include, path, re_path
from extended_templates.views.pages import PageView, EditView

from .views import PdfView

if settings.DEBUG:
    urlpatterns = staticfiles_urlpatterns() \
        + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns = [
        re_path(r'^%s(?P<path>.*)$' % settings.STATIC_URL.lstrip('/'),
            serve, kwargs={'document_root': settings.STATIC_ROOT}),
        re_path(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'),
            serve, kwargs={'document_root': settings.MEDIA_ROOT})
    ]

urlpatterns += [
    re_path(r'(?P<path>favicon.ico)', serve,
        kwargs={'document_root': settings.STATIC_ROOT if settings.STATIC_ROOT
            else 'testsite/static'}),
    path('app/', PageView.as_view(template_name='index.html')),
    path('', include('deployutils.apps.django_deployutils.mockup.urls')),
    path('', include('extended_templates.urls')),
    re_path(r'^edit(?P<page>\S+)?', EditView.as_view(),
        name='extended_templates_edit'),
    path('content/', PageView.as_view(template_name='index.html')),
    path('pdf/', PdfView.as_view()),
    re_path(r'^$', PageView.as_view(template_name='index.html'),
        name='homepage'),
]
