from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin

urlpatterns = patterns('{{ project }}.views',
    url(r'^$', 'main'),
)
