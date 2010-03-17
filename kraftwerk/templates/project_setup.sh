export PROJECT="{{ project.title }}"
export ROOT="/web/$PROJECT"
export SITE_SERVICE="/etc/service/$PROJECT"

{% if new -%}
virtualenv $ROOT
chown web:web $ROOT
{%- endif %}

{% if project.config.packages %}
$ROOT/bin/pip install{% if upgrade_packages %} -U{% endif %} -r "$ROOT/REQUIREMENTS"
{% endif %}

cat > /etc/nginx/sites-enabled/$PROJECT << "EOF"
{% include 'nginx.conf' %}
EOF

mkdir -p /var/service/$PROJECT
cat > /var/service/$PROJECT/run << "EOF"
{% include 'gunicorn.sh' %}
EOF

{% if new -%}
ln -s /var/service/$PROJECT $SITE_SERVICE
chmod +x $SITE_SERVICE/run
{% else %}
  {%- if restart -%}
sv restart $SITE_SERVICE
  {%- else %}
sv hup $SITE_SERVICE
  {%- endif -%}
{%- endif %}

/etc/init.d/nginx reload