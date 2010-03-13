from os.path import abspath, join, dirname

# Assuming site_root/project/settings/common.py
#          site_root/var/

SITE_ID = 1

PROJECT_ROOT = dirname(__file__)
SITE_ROOT = abspath(join(PROJECT_ROOT, '..'))

SECRET_KEY = '{{ secret }}'

ROOT_URLCONF = '{{ project }}.urls'

MEDIA_ROOT = join(SITE_ROOT, 'uploads')
MEDIA_URL = '/uploads/'
STATIC_ROOT = join(PROJECT_ROOT, 'static')
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'

USE_I18N = False

TIME_ZONE = 'UTC'

DEBUG = SERVE_MEDIA = TEMPLATE_DEBUG = True

INSTALLED_APPS = ()
