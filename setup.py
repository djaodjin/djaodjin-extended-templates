# Copyright (c) 2021, Djaodjin Inc.
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

from distutils.core import setup

import extended_templates

requirements = []
with open('./requirements.txt') as requirements_txt:
    for line in requirements_txt:
        prerequisite = line.split('#')[0].strip()
        if prerequisite:
            requirements += [prerequisite]

setup(
    name='djaodjin-extended-templates',
    version=extended_templates.__version__,
    author='The DjaoDjin Team',
    author_email='support@djaodjin.com',
    install_requires=requirements,
    packages=[
        'extended_templates',
        'extended_templates.api',
        'extended_templates.backends',
        'extended_templates.management',
        'extended_templates.management.commands',
        'extended_templates.templatetags',
        'extended_templates.urls',
        'extended_templates.urls.api',
        'extended_templates.urls.views',
        'extended_templates.views'],
    package_data={'extended_templates': [
        'static/js/*.js',
        'templates/extended_templates/*.html',
        'templates/django/*.html',
        'templates/jinja2/*.html',
    ]},
    url='https://github.com/djaodjin/djaodjin-extended-templates/',
    download_url='https://github.com/djaodjin/djaodjin-extended-templates'\
'/tarball/%s' % extended_templates.__version__,
    license='BSD',
    description="DjaoDjin's Template wrappers for HTML email and PDF templates",
    long_description=open('README.md').read(),
)
