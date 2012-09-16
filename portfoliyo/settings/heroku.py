from .base import *

import os
import urlparse
env = lambda key, returntype=str: returntype(os.environ[key])

DATABASES = dict(default={})
def parse_database_url(database, environment_variable='DATABASE_URL'):
    url = urlparse.urlparse(env(environment_variable))
    database.update({
        'NAME': url.path[1:],
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname,
        'PORT': url.port,
        'ENGINE' : {
            'postgres': 'django.db.backends.postgresql_psycopg2',
            'mysql': 'django.db.backends.mysql',
            'sqlite': 'django.db.backends.sqlite3',
        }[url.scheme],
    })
parse_database_url(DATABASES['default'])
del parse_database_url

# pylibmc can't be imported at build time, so we need a fallback
try:
    import pylibmc
except ImportError:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django_pylibmc.memcached.PyLibMCCache',
        }
    }

DEBUG = False
TEMPLATE_DEBUG = False

# This email address will get emailed on 500 server errors.
ADMINS = [
    ('Admin', env('ADMIN_ERROR_EMAILS')),
]

SECRET_KEY = env('DJANGO_SECRET_KEY')

# SSL
SESSION_COOKIE_SECURE = True
#SECURE_HSTS_SECONDS = 3600
#SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_FRAME_DENY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# staticfiles / compressor
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_QUERYSTRING_AUTH = False
AWS_HEADERS = {
    'Expires': 'Thu, 15 Apr 2020 20:00:00 GMT',
}
AWS_IS_GZIPPED = True
STATIC_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_URL = STATIC_URL
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_STORAGE = 'portfoliyo.storage.CachedS3BotoStorage'
STATICFILES_STORAGE = COMPRESS_STORAGE

# Mailgun
EMAIL_HOST = env('MAILGUN_SMTP_SERVER')
EMAIL_PORT = env('MAILGUN_SMTP_PORT')
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('MAILGUN_SMTP_LOGIN')
EMAIL_HOST_PASSWORD = env('MAILGUN_SMTP_PASSWORD')

# Twilio
PORTFOLIYO_SMS_BACKEND = 'portfoliyo.sms.twilio.TwilioSMSBackend'
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN')
PORTFOLIYO_SMS_DEFAULT_FROM = env('PORTFOLIYO_SMS_DEFAULT_FROM')

# Pusher
PUSHER_APPID = env('PUSHER_APPID')
PUSHER_KEY = env('PUSHER_KEY')
PUSHER_SECRET = env('PUSHER_SECRET')

# Sentry/Raven
INSTALLED_APPS += ['raven.contrib.django']
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

GOOGLE_ANALYTICS_ID=env('GOOGLE_ANALYTICS_ID')