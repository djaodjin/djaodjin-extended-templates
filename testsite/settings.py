"""
Django settings for testsite project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import logging, os, re, sys

from deployutils.configs import load_config, update_settings
from extended_templates.compat import reverse_lazy


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RUN_DIR = os.getenv('RUN_DIR', os.getcwd())
DB_NAME = os.path.join(RUN_DIR, 'db.sqlite')

DEBUG = True
ALLOWED_HOSTS = ('*',)
APP_NAME = os.path.basename(os.path.dirname(__file__))
ASSETS_CDN = {}

update_settings(sys.modules[__name__],
    load_config(APP_NAME, 'credentials', 'site.conf', verbose=True))

if not hasattr(sys.modules[__name__], "SECRET_KEY"):
    from random import choice
    SECRET_KEY = "".join([choice(
        "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)])

JWT_SECRET_KEY = SECRET_KEY
JWT_ALGORITHM = 'HS256'

# SECURITY WARNING: don't run with debug turned on in production!
if os.getenv('DEBUG'):
    # Enable override on command line.
    DEBUG = bool(int(os.getenv('DEBUG')) > 0)

# Applications
# ------------
INSTALLED_APPS = (
    'django_extensions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'extended_templates',
    'storages',
    'testsite',
)

LOG_HANDLER = {
    'level': 'DEBUG',
    'formatter': 'request_format',
    'filters': ['request'],
    'class':'logging.StreamHandler',
}
if hasattr(sys.modules[__name__], 'LOG_FILE') and LOG_FILE:
    if DEBUG:
        sys.stderr.write("writing log into %s ...\n" % LOG_FILE)
    LOG_HANDLER.update({
        'class':'logging.handlers.WatchedFileHandler',
        'filename': LOG_FILE
    })

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        # Add an unbound RequestFilter.
        'request': {
            '()': 'deployutils.apps.django_deployutils.logging.RequestFilter',
        },
    },
    'formatters': {
        'simple': {
            'format': 'X X %(levelname)s [%(asctime)s] %(message)s',
            'datefmt': '%d/%b/%Y:%H:%M:%S %z'
        },
        'request_format': {
            'format': 'gunicorn.' + APP_NAME + '.app: [%(process)d]'\
                ' %(levelname)s %(remote_addr)s %(username)s [%(asctime)s]'\
                ' %(message)s "%(http_user_agent)s"',
            'datefmt': '%d/%b/%Y:%H:%M:%S %z'
        }
    },
    'handlers': {
        'db_log': {
            'level': 'DEBUG',
            'formatter': 'simple',
            'filters': ['require_debug_true'],
            'class':'logging.StreamHandler',
        },
        'log': LOG_HANDLER,
    },
    'loggers': {
        'deployutils.perf': {
            'handlers': ['log'],
            'level': 'INFO',
            'propagate': False
        },
        'deployutils': {
            'handlers': ['db_log'],
            'level': 'INFO',
            'propagate': False
        },
        'extended_templates': {
            'handlers': [],
            'level': 'INFO',
        },
#        'django.db.backends': {
#           'handlers': ['db_log'],
#           'level': 'DEBUG',
#           'propagate': False
#        },
        'django.request': {
            'handlers': [],
            'level': 'ERROR',
        },
        # If we don't disable 'django' handlers here, we will get an extra
        # copy on stderr.
        'django': {
            'handlers': [],
        },
        # This is the root logger.
        # The level will only be taken into account if the record is not
        # propagated from a child logger.
        #https://docs.python.org/2/library/logging.html#logging.Logger.propagate
        '': {
            'handlers': ['log'],
            'level': 'INFO'
        },
    },
}

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'deployutils.apps.django_deployutils.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'testsite.urls'
WSGI_APPLICATION = 'testsite.wsgi.application'


FILE_UPLOAD_HANDLERS = (
    "extended_templates.uploadhandler.ProgressBarUploadHandler",
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
)

if 'AWS_STORAGE_BUCKET_NAME' in locals():
    DEFAULT_FILE_STORAGE = 'storages.backends.s3.S3Storage'

# XXX - to define
FILE_UPLOAD_MAX_MEMORY_SIZE = 41943040


# Static assets (CSS, JavaScript, Images)
# --------------------------------------
HTDOCS = os.path.join(BASE_DIR, 'htdocs')

STATIC_URL = '/static/'
APP_STATIC_ROOT = HTDOCS + '/static'
if DEBUG:
    STATIC_ROOT = ''
    # Additional locations of static files
    STATICFILES_DIRS = (APP_STATIC_ROOT, HTDOCS,)
else:
    STATIC_ROOT = APP_STATIC_ROOT

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = HTDOCS + '/media'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

#
# Templates
# ---------
TEMPLATE_DEBUG = True

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request'
)

TEMPLATES_DIRS = (
    os.path.join(RUN_DIR, 'themes/%s/templates' % APP_NAME),
    os.path.join(BASE_DIR, 'testsite/templates'),
)

TEMPLATES_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# Django 1.8+
TEMPLATES = [
    {
        'NAME': 'eml',
        'BACKEND': 'extended_templates.backends.eml.EmlEngine',
        'DIRS': TEMPLATES_DIRS,
        'OPTIONS': {
            'engine': 'html',
        }
    },
    {
        'NAME': 'pdf',
        'BACKEND': 'extended_templates.backends.pdf.PdfEngine',
        'DIRS': TEMPLATES_DIRS,
        'OPTIONS': {
            'loaders': TEMPLATES_LOADERS,
        }
    },
    {
        'NAME': 'html',
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': TEMPLATES_DIRS,
        'OPTIONS': {
            'environment': 'testsite.jinja2.environment'
        }
    }
]


# Database
# --------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DB_NAME,
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# API settings
# ------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'deployutils.apps.django_deployutils.authentication.JWTAuthentication',
        # `rest_framework.authentication.SessionAuthentication` is the last
        # one in the list because it will raise a PermissionDenied if the CSRF
        # is absent.
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.PageNumberPagination',
    'NON_FIELD_ERRORS_KEY': 'detail',
    'ORDERING_PARAM': 'o',
    'PAGE_SIZE': 25,
    'SEARCH_PARAM': 'q',
}

# Internationalization
# --------------------
FILE_CHARSET = 'utf-8'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Session settings
# ----------------
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
SESSION_ENGINE = 'deployutils.apps.django_deployutils.backends.jwt_session_store'

# Authentication
# --------------
# The Django Middleware expects to find the authentication backend
# before returning an authenticated user model.
AUTHENTICATION_BACKENDS = (
    'deployutils.apps.django_deployutils.backends.auth.ProxyUserBackend',
)

DEPLOYUTILS = {
    'APP_NAME': APP_NAME,
    # Hardcoded mockups here.
    'MOCKUP_SESSIONS': {
        'donny': {
            'username': 'donny',   # Profile manager for site broker
            'roles': {
                'manager': [{
                    'slug': APP_NAME,
                    'printable_name': APP_NAME,
                }]},
            'site': {
                'slug': APP_NAME,
                'printable_name': APP_NAME,
                'email': '%s@localhost.localdomain' % APP_NAME
            }
        },
    },
    'ALLOWED_NO_SESSION': [
        STATIC_URL,
        '/api/auth',
        reverse_lazy('login'),
        reverse_lazy('homepage'),
    ]
}

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/app/'
