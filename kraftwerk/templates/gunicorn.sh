#!/bin/sh

ROOT=/web/{{ project.title }}

export PYTHONPATH="$ROOT:$ROOT/lib/python2.6/site-packages"
{% for key, val in environment -%}
export CONFIG_{{ key }}="{{ val }}"
{% endfor -%}
exec 2>&1
exec gunicorn -b unix:/tmp/gunicorn.{{ project }}.sock \
    --workers {{ project.config.workers }} \
    -u web -g web \
    {{ project.config.wsgi }}
