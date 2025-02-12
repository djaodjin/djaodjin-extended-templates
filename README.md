djaodjin-extended-templates is a Django application that adds missing features
for managing Django templates.

Major Features:

- Live editing of HTML templates
- Build .css from .scss on page load
- HTML email templates
- PDF templates
- Media assets gallery
- Upload theme packages


Development
===========

**Attention!** (2024-10-01) Renamed `master` branch to `main`
(see [GitHub Renaming the default branch from master](https://github.com/github/renaming)).

After cloning the repository, create a virtualenv environment, install
the prerequisites, create the database then run the testsite webapp.

<pre><code>
    $ python -m venv .venv
    $ source .venv/bin/activate
    $ pip install -r testsite/requirements.txt
    $ make vendor-assets-prerequisites

    $ make initdb

    $ python manage.py runserver

    # Browse http://localhost:8000/
    # Start edit live templates

</code></pre>

Configure the settings to connect to your e-mail server,
then run the sendtestemail command.

    credentials:
      EMAIL_HOST_USER =
      EMAIL_HOST_PASSWORD =
    site.conf:
      EMAIL_HOST    =
      EMAIL_PORT    =
      EMAIL_USE_TLS =
      DEFAULT_FROM_EMAIL =

Then run the ``sendtestemail`` command and look for an e-mail delivered to you
in HTML format.

    $ python manage.py sendtestemail __your_email_address__


Note that you will need to link ``podofo-flatform.cc`` with [podofo](http://podofo.sourceforge.net/)
version 0.9.3. Version 0.9.1 as shipped with many RedHat systems will link
with no error but the outputed PDF will be blank.

Release Notes
=============

Tested with

- **Python:** 3.10, **Django:** 4.2  ([LTS](https://www.djangoproject.com/download/))
- **Python:** 3.12, **Django:** 5.1  (latest)
- **Python:** 3.7,  **Django:** 3.2  (legacy)
- **Python:** 2.7,  **Django:** 1.11 (legacy) - use testsite/requirements-legacy.txt

0.4.8

  * adds support for Django 5.1
  * adds support for Django 4.2 and 5.1 to testsite
  * replaces `get_storage_class` with compat wrapper of `storages.backends`

[previous release notes](changelog)
