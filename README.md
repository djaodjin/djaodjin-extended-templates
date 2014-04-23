This code was written to simplify the generation of HTML emails and PDF
outputs from templates.

Install
=======

Add the extended_templates to your INSTALLED_APPS.

    settings.py:

        INSTALLED_APPS = (
            ...
            'extended_templates',
        )

Development
===========

After cloning the repository, create a virtualenv environment, install
the prerequisites, configure the settings to your email server, then
run the sendtestemail command.

    $ virtualenv-2.7 _installTop_
    $ source _installTop_/bin/activate
    $ pip install -r requirements.txt

    # edit siteconf.py

    $ python manage.py sendtestemail __your_email_address__

