PROJECT="{{ project.name }}"
ROOT="/web/$PROJECT"
SITE_SERVICE="/var/service/$PROJECT"
PYTHON_VERSION=$(python -c 'import sys; print ".".join(map(str, sys.version_info)[:2])')

VIRTUALENV_SITEPACKAGES="$ROOT/lib/python$PYTHON_VERSION/site-packages"
requirements.txt="$ROOT/{{ project.src() }}/requirements.txt"

{% if new -%}

su - web -c "virtualenv --system-site-packages $ROOT"
su - web -c "echo $ROOT > $VIRTUALENV_SITEPACKAGES/$PROJECT.pth"

cat > /etc/nginx/sites-enabled/$PROJECT << "EOF"
{% include 'conf/nginx.conf' %}
EOF

mkdir -p $SITE_SERVICE/log/main

cat > $SITE_SERVICE/run << "EOF"
{% include 'scripts/run.sh' %}
EOF

cat > $SITE_SERVICE/log/run << "EOF"
{% include 'scripts/log.sh' %}
EOF

chmod +x $SITE_SERVICE/run
chmod +x $SITE_SERVICE/log/run
ln -s $SITE_SERVICE /etc/service/$PROJECT

{%- endif %}

su - web -c "$ROOT/bin/pip install{% if upgrade_packages %} -U{% endif %} -r $requirements.txt"
sv restart /etc/service/$PROJECT

/etc/init.d/nginx reload
