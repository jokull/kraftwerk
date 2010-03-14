from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin

urlpatterns = patterns('{{ project_title }}.views',
    url(r'^$', 'main'),
)
