#!/bin/sh

{% include "scripts/env.sh" %}
exec 2>&1
exec gunicorn -b unix:/tmp/gunicorn.{{ project }}.sock \
    --workers {{ project.config.workers }} --name {{ project }} \
    -u web -g web {{ project.config.wsgi }}
