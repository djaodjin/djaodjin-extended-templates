"""
Django settings for testsite project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

try:
    import siteconf #pylint: disable=unused-import

    # Email settings are stored in a site.py which is listed in .gitignore.
    # This avoids to inadvertently expose username and password used while
    # testing the app.
    EMAIL_HOST = siteconf.EMAIL_HOST
    EMAIL_PORT = siteconf.EMAIL_PORT
    EMAIL_USE_TLS = siteconf.EMAIL_USE_TLS

    # Default email address to use for various automated correspondence from
    # the site managers (also django-registration settings)
    DEFAULT_FROM_EMAIL = siteconf.DEFAULT_FROM_EMAIL

    # Optional SMTP authentication information for EMAIL_HOST.
    EMAIL_HOST_USER = siteconf.EMAIL_HOST_USER
    EMAIL_HOST_PASSWORD = siteconf.EMAIL_HOST_PASSWORD

except ImportError: # The module with sensitive credentials is not found.
    pass

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '#*+a0zv!^y$0qelm^r9x7*9nzhx@ec7&no)1_px#dy$!)&92t_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'extended_templates',
    'testsite',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'testsite.urls'

WSGI_APPLICATION = 'testsite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
