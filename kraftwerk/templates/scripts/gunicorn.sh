#!/bin/sh

ROOT=/web/{{ project.name }}
export PYTHONPATH=$ROOT

exec 2>&1
exec $ROOT/bin/gunicorn -b unix:/tmp/gunicorn.{{ project }}.sock \
    --workers {{ project.config.workers }} --name {{ project }} \
    -u web -g web {{ project.config.wsgi }}
