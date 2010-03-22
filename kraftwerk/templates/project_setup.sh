export PROJECT="{{ project.title }}"
export ROOT="/web/$PROJECT"
export SITE_SERVICE="/var/service/$PROJECT"
export REQUIREMENTS="$ROOT/{{ project.src() }}/REQUIREMENTS"

{% if new -%}
su - web -c "virtualenv $ROOT"
{%- endif %}

su - web -c "$ROOT/bin/pip install{% if upgrade_packages %} -U{% endif %} -r $REQUIREMENTS"

cat > /etc/nginx/sites-enabled/$PROJECT << "EOF"
{% include 'nginx.conf' %}
EOF

mkdir -p $SITE_SERVICE/log/main
cat > $SITE_SERVICE/run << "EOF"
{% include 'gunicorn.sh' %}
EOF
cat > $SITE_SERVICE/log/run << "EOF"
#!/bin/sh
exec svlogd -tt ./main
EOF

{% if new -%}
chmod +x $SITE_SERVICE/run
chmod +x $SITE_SERVICE/log/run
ln -s $SITE_SERVICE /etc/service/$PROJECT
{% else %}
  {%- if restart -%}
sv restart /etc/service/$PROJECT
  {%- else %}
sv hup /etc/service/$PROJECT
  {%- endif -%}
{%- endif %}

/etc/init.d/nginx reload