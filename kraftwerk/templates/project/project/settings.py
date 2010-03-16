from os import environ
from os.path import abspath, join, dirname

# Assuming site_root/project/settings/common.py
#          site_root/var/

SITE_ID = 1

PROJECT_ROOT = dirname(__file__)
SITE_ROOT = abspath(join(PROJECT_ROOT, '..'))

SECRET_KEY = '{{ secret }}'

ROOT_URLCONF = '{{ project_title }}.urls'

MEDIA_ROOT = environ['UPLOADS_PATH']
MEDIA_URL = '/uploads/'
STATIC_ROOT = join(PROJECT_ROOT, 'static')
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'

USE_I18N = False

TIME_ZONE = 'UTC'

DEBUG = SERVE_MEDIA = TEMPLATE_DEBUG = True

INSTALLED_APPS = ()

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_USER = environ['POSTGRES_USER']
DATABASE_NAME = environ['POSTGRES_DATABASE']
DATABASE_PASSWORD = environ['POSTGRES_PASSWORD']