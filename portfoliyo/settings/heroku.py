from .base import *

from os import environ
env = lambda key, returntype=str: returntype(environ[key])

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

CACHES = {
    'default': {
        'BACKEND': 'django_pylibmc.memcached.PyLibMCCache',
    }
}


DEBUG = False
TEMPLATE_DEBUG = False

# This email address will get emailed on 500 server errors.
ADMINS = [
    ('Admin', environ.get('ADMIN_ERROR_EMAILS')),
]

AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')

STATIC_URL = 'http://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

COMPRESS_STORAGE = 'portfoliyo.storage.CachedS3BotoStorage'
STATICFILES_STORAGE = COMPRESS_STORAGE

# A unique (and secret) key for this deployment.
SECRET_KEY = env('DJANGO_SECRET_KEY')

# If a mail server is not available at localhost:25, set these to appropriate
# values:
EMAIL_HOST = env('MAILGUN_SMTP_SERVER')
EMAIL_PORT = env('MAILGUN_SMTP_PORT')
# If the mail server configured above requires authentication and/or TLS:
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('MAILGUN_SMTP_LOGIN')
EMAIL_HOST_PASSWORD = env('MAILGUN_SMTP_PASSWORD')

# Configure Twilio SMS-sending as follows:
PORTFOLIYO_SMS_BACKEND = 'portfoliyo.sms.twilio.TwilioSMSBackend'
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN')
PORTFOLIYO_SMS_DEFAULT_FROM = env('PORTFOLIYO_SMS_DEFAULT_FROM')

# Configure Pusher as follows:
PUSHER_APPID = env('PUSHER_APPID')
PUSHER_KEY = env('PUSHER_KEY')
PUSHER_SECRET = env('PUSHER_SECRET')
