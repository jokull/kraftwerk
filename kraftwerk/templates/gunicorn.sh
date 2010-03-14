#!/bin/sh

ROOT=/web/{{ project }}

export PYTHONPATH="$ROOT:$ROOT/lib/python2.6/site-packages"
{%- for service in services -%}
{% for key, val in service.env.items -%}
export CONFIG_{{ key }}="{{ val }}"
{% endfor %}
{% endfor %}
exec 2>&1
exec gunicorn -b unix:/tmp/gunicorn.{{ project }}.sock \
    -workers {{ project.config.workers }} \
    -u web -g web {{ project.config.wsgi }}
