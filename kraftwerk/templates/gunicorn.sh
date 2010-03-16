#!/bin/sh

{% include "env.sh" %}
exec 2>&1
exec gunicorn -b unix:/tmp/gunicorn.{{ project }}.sock \
    --workers {{ project.config.workers }} \
    -u web -g web \
    {{ project.config.wsgi }}
