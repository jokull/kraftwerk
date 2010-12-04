PROJECT="{{ project.name }}"
ROOT="/web/$PROJECT"
SITE_SERVICE="/var/service/$PROJECT"
VIRTUALENV_SITEPACKAGES="$ROOT/lib/`ls -1 $ROOT/lib`/site-packages"
REQUIREMENTS="$ROOT/{{ project.src() }}/REQUIREMENTS"

{% if new -%}
su - web -c "virtualenv $ROOT"
su - web -c "echo $ROOT > $VIRTUALENV_SITEPACKAGES/$PROJECT.pth"
{%- endif %}

su - web -c "$ROOT/bin/pip install{% if upgrade_packages %} -U{% endif %} -r $REQUIREMENTS"

cat > /etc/nginx/sites-enabled/$PROJECT << "EOF"
{% include 'conf/nginx.conf' %}
EOF

{% if new -%}
mkdir -p $SITE_SERVICE/log/main
cat > $SITE_SERVICE/run << "EOF"
{% include 'scripts/run.sh' %}
EOF
{%- endif %}

cat > $SITE_SERVICE/log/run << "EOF"
{% include 'scripts/log.sh' %}
EOF

{% if new -%}
chmod +x $SITE_SERVICE/run
chmod +x $SITE_SERVICE/log/run
ln -s $SITE_SERVICE /etc/service/$PROJECT
{% else %}
sv restart /etc/service/$PROJECT
{%- endif %}

/etc/init.d/nginx reload