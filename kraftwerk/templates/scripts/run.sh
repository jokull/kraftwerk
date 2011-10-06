#!/bin/sh

{% include "scripts/env.sh" %}
export UWSGI_SOCKET=/tmp/uwsgi.{{ project }}.sock
export UWSGI_MODULE={{ project.config.module }}
export UWSGI_CALLABLE={{ project.config.callable }}
export UWSGI_MASTER=1
export UWSGI_PROCESSES={{ project.config.workers }}
export UWSGI_MEMORY_REPORT=1
export UWSGI_HARAKIRI=30

export PYTHONPATH=$VIRTUALENV_SITEPACKAGES

exec 2>&1
exec uwsgi  --reload-os-env -C --uid web --gid web -H $ROOT
